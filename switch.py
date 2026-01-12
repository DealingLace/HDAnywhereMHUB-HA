"""Switch platform for HDAnywhere MHUB (legacy power control)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN, MANUFACTURER, MODEL
from .coordinator import MHUBDataUpdateCoordinator
from .exceptions import MHUBException

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MHUB switch entity from config entry.

    This creates a single switch entity for power control of the entire device.
    This is a legacy feature - users should prefer media player entities for control.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: MHUBDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    device_name = entry.data.get(CONF_NAME)
    host = entry.data[CONF_HOST]

    # Create single switch entity for device power control
    async_add_entities([HDAnywhereMHUBSwitch(coordinator, entry.entry_id, device_name, host)])

    _LOGGER.info("Set up MHUB switch entity")


class HDAnywhereMHUBSwitch(CoordinatorEntity[MHUBDataUpdateCoordinator], SwitchEntity):
    """Representation of a HDAnywhere MHUB Switch for power control.

    This switch controls the entire MHUB device power state.
    Uses coordinator for efficient shared state management.

    Note: This is a legacy entity type. Media player entities provide
    the same functionality with additional features.
    """

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(
        self,
        coordinator: MHUBDataUpdateCoordinator,
        entry_id: str,
        device_name: str,
        host: str,
    ) -> None:
        """Initialize the switch.

        Args:
            coordinator: Data update coordinator
            entry_id: Config entry ID
            device_name: MHUB device name
            host: MHUB IP address
        """
        super().__init__(coordinator)

        self._device_name = device_name
        self._host = host

        # Entity naming
        self._attr_name = "Power"

        # Unique ID for entity registry
        self._attr_unique_id = f"{device_name}_{host.replace('.', '_')}_switch".replace(" ", "_")

        # Device info for grouping with other MHUB entities
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": device_name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "configuration_url": f"http://{host}",
        }

        _LOGGER.debug("Initialized MHUB switch entity for %s", device_name)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.device_state.get("power", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "device": self._device_name,
            "host": self._host,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on.

        Args:
            **kwargs: Additional arguments (not used)
        """
        _LOGGER.info("Turning on MHUB device via switch")

        try:
            await self.coordinator.async_set_power(True)
            _LOGGER.info("Successfully turned on MHUB device")
        except MHUBException as err:
            _LOGGER.error("Failed to turn on device: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off.

        Args:
            **kwargs: Additional arguments (not used)
        """
        _LOGGER.info("Turning off MHUB device via switch")

        try:
            await self.coordinator.async_set_power(False)
            _LOGGER.info("Successfully turned off MHUB device")
        except MHUBException as err:
            _LOGGER.error("Failed to turn off device: %s", err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        This is called automatically when coordinator data changes.
        """
        _LOGGER.debug("Received coordinator update for switch")
        self.async_write_ha_state()
