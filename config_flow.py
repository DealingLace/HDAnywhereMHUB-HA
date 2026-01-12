"""Config flow for HDAnywhere MHUB integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
import homeassistant.helpers.device_registry as dr

from .api_client import MHUBApiClient
from .const import (
    CONF_API_VERSION,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ERROR_ALREADY_CONFIGURED,
    ERROR_CANNOT_CONNECT,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)
from .exceptions import MHUBConnectionError, MHUBException, MHUBTimeoutError

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Args:
        hass: Home Assistant instance
        data: User input from config flow

    Returns:
        Dictionary with device information

    Raises:
        MHUBConnectionError: Cannot connect to device
        MHUBTimeoutError: Connection timed out
    """
    host = data[CONF_HOST]

    # Create API client with temporary session
    async with aiohttp.ClientSession() as session:
        client = MHUBApiClient(host, session=session)

        try:
            # Test connection
            if not await client.test_connection():
                raise MHUBConnectionError("Cannot connect to MHUB device")

            # Fetch system info to get device name and details
            system_info = await client.get_system_info()
            mhub_info = system_info.get("mhub", {})

            device_name = mhub_info.get("mhub_name", DEFAULT_NAME)
            firmware_version = mhub_info.get("firmware_version", "Unknown")
            hardware_version = mhub_info.get("hardware_version", "Unknown")
            serial_number = mhub_info.get("serial_number", host.replace(".", "_"))

            _LOGGER.info(
                "Successfully connected to MHUB: %s (FW: %s, HW: %s)",
                device_name,
                firmware_version,
                hardware_version,
            )

            return {
                "title": device_name,
                "device_name": device_name,
                "firmware_version": firmware_version,
                "hardware_version": hardware_version,
                "serial_number": serial_number,
            }

        finally:
            await client.close()


class MHUBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HDAnywhere MHUB."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step when user initiates setup.

        Args:
            user_input: User provided configuration

        Returns:
            FlowResult to show form or create entry
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            # Check if already configured
            await self.async_set_unique_id(host.replace(".", "_"))
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except MHUBConnectionError:
                _LOGGER.error("Cannot connect to MHUB at %s", host)
                errors["base"] = ERROR_CANNOT_CONNECT
            except MHUBTimeoutError:
                _LOGGER.error("Timeout connecting to MHUB at %s", host)
                errors["base"] = ERROR_TIMEOUT
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN
            else:
                # Store the device information
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: host,
                        CONF_NAME: info["device_name"],
                        "firmware_version": info["firmware_version"],
                        "hardware_version": info["hardware_version"],
                        "serial_number": info["serial_number"],
                    },
                )

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=self._discovered_host or ""): str,
            }),
            errors=errors,
            description_placeholders={
                "name": self._discovered_name or DEFAULT_NAME,
            },
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery.

        Args:
            discovery_info: Discovery information from zeroconf

        Returns:
            FlowResult to continue config flow
        """
        _LOGGER.debug("Discovered MHUB device via zeroconf: %s", discovery_info)

        host = discovery_info.host
        name = discovery_info.name.replace("._http._tcp.local.", "").replace("._hda._tcp.local.", "")

        # Check if already configured
        await self.async_set_unique_id(host.replace(".", "_"))
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        # Store discovered info and continue to confirm step
        self._discovered_host = host
        self._discovered_name = name

        # Try to get the actual device name
        try:
            async with aiohttp.ClientSession() as session:
                client = MHUBApiClient(host, session=session)
                try:
                    system_info = await client.get_system_info()
                    mhub_info = system_info.get("mhub", {})
                    self._discovered_name = mhub_info.get("mhub_name", name)
                finally:
                    await client.close()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Could not fetch device name during discovery: %s", err)

        self.context.update({
            "title_placeholders": {
                "name": self._discovered_name,
            }
        })

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle confirmation of discovered device.

        Args:
            user_input: User confirmation

        Returns:
            FlowResult to create entry or show form
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass,
                    {CONF_HOST: self._discovered_host},
                )
            except MHUBConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except MHUBTimeoutError:
                errors["base"] = ERROR_TIMEOUT
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: self._discovered_host,
                        CONF_NAME: info["device_name"],
                        "firmware_version": info["firmware_version"],
                        "hardware_version": info["hardware_version"],
                        "serial_number": info["serial_number"],
                    },
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._discovered_name,
                "host": self._discovered_host,
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MHUBOptionsFlowHandler:
        """Get the options flow for this handler.

        Args:
            config_entry: Config entry instance

        Returns:
            Options flow handler
        """
        return MHUBOptionsFlowHandler(config_entry)


class MHUBOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for MHUB integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow.

        Args:
            config_entry: Config entry instance
        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options.

        Args:
            user_input: User provided options

        Returns:
            FlowResult to show form or save options
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values or defaults
        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL.total_seconds(),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=scan_interval,
                ): vol.All(cv.positive_int, vol.Range(min=5, max=300)),
            }),
            description_placeholders={
                "name": self.config_entry.data.get(CONF_NAME, DEFAULT_NAME),
            },
        )
