"""Media Player platform for HDAnywhere MHUB."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ARC_INPUT,
    ATTR_AUTO_SWITCH_MODE,
    ATTR_MHUB_NAME,
    ATTR_OUTPUT_ID,
    ATTR_OUTPUT_TYPE,
    ATTR_ZONE_LABEL,
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import MHUBData, MHUBDataUpdateCoordinator
from .exceptions import MHUBException

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MHUB media player entities from config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: MHUBDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    device_name = entry.data.get(CONF_NAME)
    host = entry.data[CONF_HOST]

    # Create media player entity for each active output
    entities: list[HDAnywhereMHUBMediaPlayer] = []

    for output in coordinator.data.available_outputs:
        entities.append(
            HDAnywhereMHUBMediaPlayer(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                device_name=device_name,
                host=host,
                output_data=output,
                available_inputs=coordinator.data.available_inputs,
            )
        )

    async_add_entities(entities)

    _LOGGER.info("Set up %d MHUB media player entities", len(entities))


class HDAnywhereMHUBMediaPlayer(CoordinatorEntity[MHUBDataUpdateCoordinator], MediaPlayerEntity):
    """Representation of a HDAnywhere MHUB Media Player.

    Uses coordinator for efficient shared state management and automatic updates.
    Fully async for optimal Home Assistant performance.
    """

    _attr_has_entity_name = True
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(
        self,
        coordinator: MHUBDataUpdateCoordinator,
        entry_id: str,
        device_name: str,
        host: str,
        output_data: dict[str, Any],
        available_inputs: dict[str, str],
    ) -> None:
        """Initialize the media player.

        Args:
            coordinator: Data update coordinator
            entry_id: Config entry ID
            device_name: MHUB device name
            host: MHUB IP address
            output_data: Output configuration data
            available_inputs: Available input sources
        """
        super().__init__(coordinator)

        self._entry_id = entry_id
        self._device_name = device_name
        self._host = host

        # Output information
        self._output_id = output_data[ATTR_OUTPUT_ID]
        self._output_type = output_data[ATTR_OUTPUT_TYPE]
        self._zone_label = output_data[ATTR_ZONE_LABEL]
        self._arc_input = output_data.get(ATTR_ARC_INPUT)
        self._auto_switch_mode = output_data.get(ATTR_AUTO_SWITCH_MODE, False)

        # Entity naming: "Zone Name (Output ID) (Type)"
        self._attr_name = f"{self._zone_label} ({self._output_id.upper()}) ({self._output_type})"

        # Unique ID for entity registry
        self._attr_unique_id = (
            f"{device_name}_{host.replace('.', '_')}_{self._output_id}".replace(" ", "_")
        )

        # Device info for grouping entities under the MHUB device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": device_name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "configuration_url": f"http://{host}",
        }

        # Supported features
        self._attr_supported_features = (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

        _LOGGER.debug(
            "Initialized media player: %s (output: %s, type: %s)",
            self._attr_name,
            self._output_id,
            self._output_type,
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the media player."""
        if self.coordinator.data.device_state.get("power"):
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def source(self) -> str | None:
        """Return the current input source.

        Note: The MHUB API doesn't provide per-output source state,
        so this shows as unknown. Consider this a future enhancement
        if the API adds support for it.
        """
        # TODO: Track source locally after select_source is called
        # The API doesn't provide per-output source information
        return None

    @property
    def source_list(self) -> list[str]:
        """Return list of available input sources."""
        return list(self.coordinator.data.available_inputs.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            ATTR_OUTPUT_ID: self._output_id,
            ATTR_OUTPUT_TYPE: self._output_type,
            ATTR_ZONE_LABEL: self._zone_label,
            ATTR_ARC_INPUT: self._arc_input,
            ATTR_AUTO_SWITCH_MODE: self._auto_switch_mode,
            ATTR_MHUB_NAME: self._device_name,
        }

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        _LOGGER.info("Turning on MHUB device")

        try:
            await self.coordinator.async_set_power(True)
            _LOGGER.info("Successfully turned on MHUB device")
        except MHUBException as err:
            _LOGGER.error("Failed to turn on device: %s", err)

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        _LOGGER.info("Turning off MHUB device")

        try:
            await self.coordinator.async_set_power(False)
            _LOGGER.info("Successfully turned off MHUB device")
        except MHUBException as err:
            _LOGGER.error("Failed to turn off device: %s", err)

    async def async_select_source(self, source: str) -> None:
        """Select input source.

        Args:
            source: Source name to switch to
        """
        # Find the input ID corresponding to the selected source name
        input_mapping = {v: k for k, v in self.coordinator.data.available_inputs.items()}
        input_id = input_mapping.get(source)

        if input_id is None:
            _LOGGER.error(
                "Invalid source selected: %s. Available sources: %s",
                source,
                self.coordinator.data.available_inputs,
            )
            return

        _LOGGER.info("Switching output %s to input %s (%s)", self._output_id, input_id, source)

        try:
            await self.coordinator.async_switch_output(self._output_id, input_id)
            _LOGGER.info("Successfully switched to source: %s", source)
        except MHUBException as err:
            _LOGGER.error("Failed to switch source: %s", err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        This is called automatically when coordinator data changes.
        """
        _LOGGER.debug("Received coordinator update for %s", self._attr_name)
        self.async_write_ha_state()
