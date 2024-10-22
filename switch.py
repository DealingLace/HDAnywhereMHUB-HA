import requests
import logging
import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_IP_ADDRESS
import homeassistant.helpers.config_validation as cv

# LEGACY OPTION, CONFIGURED UNDER SWITCH DOMAIN

_LOGGER = logging.getLogger(__name__)

# Define the domain of the component
DOMAIN = "hdanywheremhub"

# Configuration schema for the component
PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): cv.string
}, extra=vol.ALLOW_EXTRA)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the HDAnywhere MHUB switch platform."""
    ip_address = config.get(CONF_IP_ADDRESS)
    add_entities([HDAnywhereMHUBSwitch(ip_address)], True)


class HDAnywhereMHUBSwitch(SwitchEntity):
    """Representation of a REST API controlled switch for HDAnywhere MHUB."""

    def __init__(self, ip_address):
        """Initialize the switch."""
        self._ip_address = ip_address
        self._state = False
        self.base_url = f"http://{self._ip_address}/api"

    @property
    def name(self):
        """Return the name of the switch."""
        return f"MHUB Switch {self._ip_address}"

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        url = f"{self.base_url}/power/1/"  # Turn On (fix this to ensure "0" is ON)
        try:
            response = requests.post(url)
            if response.status_code == 200:
                _LOGGER.info("Turn on command sent successfully.")
                self._state = True  # Ensure state reflects the device being ON
                self.update()  # Manually check the device state after the command
            else:
                _LOGGER.error(f"Failed to turn on the switch: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error turning on switch: {e}")

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        url = f"{self.base_url}/power/0/"  # Turn Off (fix this to ensure "1" is OFF)
        try:
            response = requests.post(url)
            if response.status_code == 200:
                _LOGGER.info("Turn off command sent successfully.")
                self._state = False  # Ensure state reflects the device being OFF
                self.update()  # Manually check the device state after the command
            else:
                _LOGGER.error(f"Failed to turn off the switch: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error turning off switch: {e}")

    def update(self):
        """Fetch the latest state of the switch from the device."""
        url = f"{self.base_url}/data/0/"  # Get State
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Use the nested structure to get the power status
                # Ensure True means "on" and False means "off"
                self._state = data['data']['power'] == True  
                _LOGGER.info(f"Switch state updated: {'on' if self._state else 'off'}")
            else:
                _LOGGER.error(f"Failed to update switch state: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error updating switch state: {e}")
