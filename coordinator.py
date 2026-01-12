"""Data update coordinator for HDAnywhere MHUB."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_client import MHUBApiClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .exceptions import MHUBException

_LOGGER = logging.getLogger(__name__)


@dataclass
class MHUBData:
    """Class to hold MHUB device data."""

    system_info: dict[str, Any]
    zone_data: dict[int, dict[str, Any]]
    device_state: dict[str, Any]
    available_inputs: dict[str, str]
    available_outputs: list[dict[str, Any]]


class MHUBDataUpdateCoordinator(DataUpdateCoordinator[MHUBData]):
    """Class to manage fetching MHUB data from the device.

    This coordinator ensures all entities share a single polling cycle,
    reducing network traffic and improving efficiency.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: MHUBApiClient,
        device_name: str,
        scan_interval: timedelta = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            client: MHUB API client
            device_name: Name of the MHUB device
            scan_interval: Interval between updates
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_name}",
            update_interval=scan_interval,
        )
        self.client = client
        self.device_name = device_name
        self._system_info_cache: dict[str, Any] | None = None
        self._zone_data_cache: dict[int, dict[str, Any]] | None = None

    async def _async_update_data(self) -> MHUBData:
        """Fetch data from MHUB device.

        This is called automatically by Home Assistant based on update_interval.
        System info and zone data are cached since they rarely change.

        Returns:
            MHUBData object with current device state

        Raises:
            UpdateFailed: Update failed due to communication error
        """
        try:
            # Fetch device state (this changes frequently)
            device_state = await self.client.get_device_state()

            # Fetch system info only if not cached
            if self._system_info_cache is None:
                _LOGGER.debug("Fetching system info (not cached)")
                self._system_info_cache = await self.client.get_system_info()
            else:
                _LOGGER.debug("Using cached system info")

            system_info = self._system_info_cache

            # Fetch zone data only if not cached
            if self._zone_data_cache is None:
                _LOGGER.debug("Fetching zone data (not cached)")
                self._zone_data_cache = await self.client.get_zone_data()
            else:
                _LOGGER.debug("Using cached zone data")

            zone_data = self._zone_data_cache

            # Process available inputs
            available_inputs = self._process_inputs(system_info.get("io_data", {}).get("input_video", []))

            # Process available outputs
            available_outputs = self._process_outputs(
                system_info.get("io_data", {}).get("output_video", []),
                zone_data,
            )

            _LOGGER.debug(
                "Successfully updated data: power=%s, inputs=%d, outputs=%d",
                device_state.get("power"),
                len(available_inputs),
                len(available_outputs),
            )

            return MHUBData(
                system_info=system_info,
                zone_data=zone_data,
                device_state=device_state,
                available_inputs=available_inputs,
                available_outputs=available_outputs,
            )

        except MHUBException as err:
            _LOGGER.error("Error communicating with MHUB device: %s", err)
            raise UpdateFailed(f"Error communicating with device: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error updating MHUB data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _process_inputs(self, input_data: list[dict[str, Any]]) -> dict[str, str]:
        """Process input data and return a mapping of input IDs to labels.

        Args:
            input_data: List of input configurations from the device

        Returns:
            Dictionary mapping input IDs to their display labels
        """
        available_inputs: dict[str, str] = {}

        for input_info in input_data:
            # Check if any label has a 'show' attribute
            any_show_attribute = any("show" in label for label in input_info.get("labels", []))

            for input_label in input_info.get("labels", []):
                input_id = input_label.get("id")
                label = input_label.get("label", f"Input {input_id}")

                # Include input if:
                # 1. No 'show' attribute exists anywhere (show all), OR
                # 2. This specific input has show=True
                if not any_show_attribute or input_label.get("show", True):
                    available_inputs[str(input_id)] = label

        _LOGGER.debug("Processed %d available inputs", len(available_inputs))
        return available_inputs

    def _process_outputs(
        self,
        output_data: list[dict[str, Any]],
        zone_mapping: dict[int, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Process output data and return list of active outputs with zone info.

        Args:
            output_data: List of output configurations from the device
            zone_mapping: Mapping of output IDs to zone information

        Returns:
            List of output dictionaries with zone information
        """
        available_outputs: list[dict[str, Any]] = []

        for output in output_data:
            output_type = output.get("type", "unknown")

            for label in output.get("labels", []):
                output_id = label.get("id")

                # Only include outputs that are part of an active zone
                if output_id in zone_mapping:
                    zone_info = zone_mapping[output_id]
                    available_outputs.append({
                        "output_id": output_id,
                        "output_type": output_type,
                        "zone_label": zone_info.get("zone_label", "Unknown Zone"),
                        "arc_input": zone_info.get("arc_input"),
                        "auto_switch_mode": zone_info.get("auto_switch_mode", False),
                    })

        _LOGGER.debug("Processed %d active outputs", len(available_outputs))
        return available_outputs

    async def async_refresh_system_info(self) -> None:
        """Force refresh of system info and zone data.

        This should be called when sources or zones are reconfigured.
        """
        _LOGGER.info("Forcing refresh of system info and zone data")
        self._system_info_cache = None
        self._zone_data_cache = None
        await self.async_request_refresh()

    async def async_set_power(self, power_on: bool) -> None:
        """Set power state and immediately update coordinator data.

        Args:
            power_on: True to power on, False to power off
        """
        await self.client.set_power(power_on)
        # Request immediate refresh to update all entities
        await self.async_request_refresh()

    async def async_switch_output(self, output_id: str, input_id: str) -> None:
        """Switch output to input and immediately update coordinator data.

        Args:
            output_id: Output identifier
            input_id: Input identifier
        """
        await self.client.switch_output(output_id, input_id)
        # Request immediate refresh to update all entities
        await self.async_request_refresh()
