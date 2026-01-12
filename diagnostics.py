"""Diagnostics support for HDAnywhere MHUB."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import COORDINATOR, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    This data is shown when users download diagnostics from the UI,
    helping with troubleshooting and bug reports.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        Dictionary with diagnostic information
    """
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    # Gather diagnostic data
    diagnostics_data = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
        },
        "device_state": {
            "power": coordinator.data.device_state.get("power"),
        },
        "system_info": {
            "mhub_name": coordinator.data.system_info.get("mhub", {}).get("mhub_name"),
            "firmware_version": coordinator.data.system_info.get("mhub", {}).get("firmware_version"),
            "hardware_version": coordinator.data.system_info.get("mhub", {}).get("hardware_version"),
        },
        "configuration": {
            "available_inputs": len(coordinator.data.available_inputs),
            "available_outputs": len(coordinator.data.available_outputs),
            "input_list": list(coordinator.data.available_inputs.values()),
            "output_zones": [
                {
                    "output_id": output["output_id"],
                    "output_type": output["output_type"],
                    "zone_label": output["zone_label"],
                    "auto_switch_mode": output.get("auto_switch_mode", False),
                }
                for output in coordinator.data.available_outputs
            ],
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
    }

    return diagnostics_data
