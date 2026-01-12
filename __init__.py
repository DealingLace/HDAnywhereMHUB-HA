"""The HDAnywhere MHUB integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.entity_registry as er

from .api_client import MHUBApiClient
from .const import (
    ATTR_INPUT_ID,
    ATTR_OUTPUT_ID,
    ATTR_TARGET_INPUT,
    ATTR_TARGET_OUTPUT,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    MHUB_CLIENT,
    MODEL,
    PLATFORMS,
    SERVICE_REFRESH_SOURCES,
    SERVICE_SWITCH_OUTPUT,
)
from .coordinator import MHUBDataUpdateCoordinator
from .exceptions import MHUBException

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_SWITCH_OUTPUT_SCHEMA = vol.Schema({
    vol.Required(ATTR_TARGET_OUTPUT): cv.string,
    vol.Required(ATTR_TARGET_INPUT): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HDAnywhere MHUB from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if setup was successful

    Raises:
        ConfigEntryNotReady: Device is not ready
    """
    host = entry.data[CONF_HOST]
    device_name = entry.data.get(CONF_NAME, host)

    _LOGGER.info("Setting up HDAnywhere MHUB integration for %s at %s", device_name, host)

    # Create API client
    client = MHUBApiClient(host)

    # Test connection
    try:
        if not await client.test_connection():
            await client.close()
            raise ConfigEntryNotReady(f"Unable to connect to MHUB at {host}")
    except MHUBException as err:
        await client.close()
        raise ConfigEntryNotReady(f"Unable to connect to MHUB at {host}: {err}") from err

    # Get scan interval from options or use default
    scan_interval_seconds = entry.options.get(
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL.total_seconds(),
    )
    scan_interval = timedelta(seconds=scan_interval_seconds)

    # Create data update coordinator
    coordinator = MHUBDataUpdateCoordinator(
        hass,
        client,
        device_name,
        scan_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and client
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        MHUB_CLIENT: client,
    }

    # Register device in device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data.get("serial_number", host.replace(".", "_")))},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=device_name,
        sw_version=entry.data.get("firmware_version"),
        hw_version=entry.data.get("hardware_version"),
        configuration_url=f"http://{host}",
    )

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass, entry)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("Successfully set up HDAnywhere MHUB integration for %s", device_name)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if unload was successful
    """
    _LOGGER.info("Unloading HDAnywhere MHUB integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close API client
        client: MHUBApiClient = hass.data[DOMAIN][entry.entry_id][MHUB_CLIENT]
        await client.close()

        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id)

        # If this was the last entry, remove services
        if not hass.data[DOMAIN]:
            for service in [SERVICE_SWITCH_OUTPUT, SERVICE_REFRESH_SOURCES]:
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change.

    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    _LOGGER.info("Reloading HDAnywhere MHUB integration due to options change")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up services for MHUB integration.

    Args:
        hass: Home Assistant instance
        entry: Config entry
    """

    async def handle_switch_output(call: ServiceCall) -> None:
        """Handle switch_output service call.

        Allows direct switching of any output to any input without
        going through entity UI.

        Args:
            call: Service call with output and input parameters
        """
        output_id = call.data[ATTR_TARGET_OUTPUT]
        input_id = call.data[ATTR_TARGET_INPUT]

        _LOGGER.info("Service call: switch output %s to input %s", output_id, input_id)

        # Get coordinator for this entry
        coordinator: MHUBDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

        try:
            await coordinator.async_switch_output(output_id, input_id)
            _LOGGER.info("Successfully switched output %s to input %s", output_id, input_id)
        except MHUBException as err:
            _LOGGER.error("Failed to switch output: %s", err)

    async def handle_refresh_sources(call: ServiceCall) -> None:
        """Handle refresh_sources service call.

        Forces a refresh of system info and zone data to pick up
        configuration changes made on the device.

        Args:
            call: Service call
        """
        _LOGGER.info("Service call: refresh sources")

        # Refresh all coordinators
        for entry_id, data in hass.data[DOMAIN].items():
            if isinstance(data, dict) and COORDINATOR in data:
                coordinator: MHUBDataUpdateCoordinator = data[COORDINATOR]
                await coordinator.async_refresh_system_info()

        _LOGGER.info("Successfully refreshed sources for all devices")

    # Register services (only once)
    if not hass.services.has_service(DOMAIN, SERVICE_SWITCH_OUTPUT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SWITCH_OUTPUT,
            handle_switch_output,
            schema=SERVICE_SWITCH_OUTPUT_SCHEMA,
        )
        _LOGGER.debug("Registered service: %s", SERVICE_SWITCH_OUTPUT)

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_SOURCES):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_SOURCES,
            handle_refresh_sources,
        )
        _LOGGER.debug("Registered service: %s", SERVICE_REFRESH_SOURCES)


# Legacy YAML configuration support (will be removed in future version)
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the HDAnywhere MHUB component (legacy).

    This is maintained for backwards compatibility but users should
    migrate to config flow setup through the UI.

    Args:
        hass: Home Assistant instance
        config: Configuration from configuration.yaml

    Returns:
        True if setup was successful
    """
    if DOMAIN not in config:
        return True

    _LOGGER.warning(
        "YAML configuration for HDAnywhere MHUB is deprecated. "
        "Please remove it from configuration.yaml and set up the integration "
        "through the UI (Configuration -> Integrations -> Add Integration)"
    )

    return True
