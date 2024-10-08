import requests
import logging
import voluptuous as vol

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import CONF_IP_ADDRESS, STATE_OFF, STATE_ON
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Define the domain of the component
DOMAIN = "hdanywheremhub"

# Configuration schema for the component
PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): cv.string
}, extra=vol.ALLOW_EXTRA)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the HDAnywhere MHUB media player platform."""
    ip_address = config.get(CONF_IP_ADDRESS)
    add_entities([HDAnywhereMHUBMediaPlayer(ip_address)], True)


class HDAnywhereMHUBMediaPlayer(MediaPlayerEntity):
    """Representation of a Media Player for HDAnywhere MHUB."""

    def __init__(self, ip_address):
        """Initialize the media player."""
        self._ip_address = ip_address
        self._state = STATE_OFF
        self._source = None
        self.base_url = f"http://{self._ip_address}/api"
        self._available_sources = {
            "1": "Input 1",
            "2": "Input 2",
            "3": "Input 3",
            "4": "Input 4",
        }

    @property
    def name(self):
        """Return the name of the media player."""
        return f"MHUB Media Player {self._ip_address}"

    @property
    def state(self):
        """Return the state of the media player."""
        return self._state

    @property
    def source(self):
        """Return the current input source."""
        return self._source

    @property
    def source_list(self):
        """Return a list of available input sources."""
        return list(self._available_sources.values())

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return (
            MediaPlayerEntityFeature.TURN_ON |
            MediaPlayerEntityFeature.TURN_OFF |
            MediaPlayerEntityFeature.SELECT_SOURCE
        )

    def turn_on(self):
        """Turn the media player on."""
        url = f"{self.base_url}/power/1/"  # Turn ON
        try:
            response = requests.post(url)
            if response.status_code == 200:
                _LOGGER.info("Turn on command sent successfully.")
                self._state = STATE_ON
                self.update()
            else:
                _LOGGER.error(f"Failed to turn on the device: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error turning on device: {e}")

    def turn_off(self):
        """Turn the media player off."""
        url = f"{self.base_url}/power/0/"  # Turn OFF
        try:
            response = requests.post(url)
            if response.status_code == 200:
                _LOGGER.info("Turn off command sent successfully.")
                self._state = STATE_OFF
                self.update()
            else:
                _LOGGER.error(f"Failed to turn off the device: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error turning off device: {e}")

    def select_source(self, source):
        """Select the input source."""
        # Map the source name back to its corresponding input number
        input_port = {v: k for k, v in self._available_sources.items()}.get(source)
        output_port = "a"  # Assuming you're controlling output A

        if input_port:
            url = f"{self.base_url}/control/switch/{output_port}/{input_port}/"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    _LOGGER.info(f"Input switched to {source}.")
                    self._source = source
                    self.update()
                else:
                    _LOGGER.error(f"Failed to switch input: {response.status_code}")
            except Exception as e:
                _LOGGER.error(f"Error switching input: {e}")
        else:
            _LOGGER.error(f"Invalid source selected: {source}")

    def update(self):
        """Fetch the latest state of the media player from the device."""
        url = f"{self.base_url}/data/0/"  # Get power state
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Check power status
                self._state = STATE_ON if data['data']['power'] else STATE_OFF
                _LOGGER.info(f"Device state updated: {'on' if self._state == STATE_ON else 'off'}")
            else:
                _LOGGER.error(f"Failed to update device state: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error updating device state: {e}")
