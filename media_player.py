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

def get_zone_data_2_1(ip_address):
    """Retrieve and return zone data from the MHUB 2.1 API."""
    try:
        url = f"http://{ip_address}/api/data/102"
        response = requests.get(url)
        if response.status_code == 200:
            zone_data = response.json().get("data", [])
            # Create a dictionary mapping output IDs to zone labels and additional info
            zone_mapping = {}
            for zone in zone_data:
                for output in zone.get("outputs", []):
                    zone_mapping[output["output_id"]] = {
                        "zone_label": zone["zone_label"],
                        "arc_input": output.get("arc_input"),
                        "auto_switch_mode": zone.get("auto_switch_mode", False)
                    }
            return zone_mapping
        else:
            _LOGGER.error(f"Failed to retrieve zone data: {response.status_code}")
    except Exception as e:
        _LOGGER.error(f"Error fetching zone data: {e}")
    return {}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the HDAnywhere MHUB media player platform."""
    ip_address = config.get(CONF_IP_ADDRESS)
    
    # Fetch zone data to map outputs to zone labels for API 2.1
    zone_mapping = get_zone_data_2_1(ip_address)

    # Fetch system information from the API
    base_url = f"http://{ip_address}/api/data/100/"
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            data = response.json()

            # Extract the MHUB name
            mhub_name = data["data"]["mhub"].get("mhub_name", "MHUB")

            # Log the data to inspect its structure
            _LOGGER.debug(f"Received system data: {data}")

            # Check if inputs and outputs exist and are in the correct format
            io_data = data["data"]["io_data"]

            inputs = io_data["input_video"]  # List of input video sources
            outputs = io_data["output_video"]  # List of output video ports

            # Create media player entities for each active zone output
            media_players = []
            for output in outputs:
                output_type = output.get("type", "unknown")
                
                # Use each label within 'labels' to create separate entities
                for label in output.get("labels", []):
                    output_id = label.get("id", "Unknown")
                    
                    # Check if this output is part of an active zone
                    if output_id not in zone_mapping:
                        continue  # Skip outputs not assigned to an active zone
                    
                    # Retrieve zone details
                    zone_details = zone_mapping[output_id]
                    zone_label = zone_details["zone_label"]

                    # Prepare available sources (input labels)
                    available_sources = {}
                    for input_data in inputs:
                        any_show_attribute = any('show' in label for label in input_data.get('labels', []))
                        for input_label in input_data.get('labels', []):
                            if not any_show_attribute or input_label.get('show', True):
                                available_sources[input_label['id']] = input_label['label']

                    # Simplified entity naming: (Zone Name) (Output ID) (Type)
                    entity_name = f"{zone_label} ({output_id}) ({output_type})"

                    # Pass both inputs and outputs to the media player
                    media_players.append(
                        HDAnywhereMHUBMediaPlayer(
                            ip_address, output_id, entity_name, available_sources, mhub_name, output_type
                        )
                    )

            add_entities(media_players, True)
        else:
            _LOGGER.error(f"Failed to retrieve system information: {response.status_code}")
    except Exception as e:
        _LOGGER.error(f"Error fetching system information: {e}")

class HDAnywhereMHUBMediaPlayer(MediaPlayerEntity):
    """Representation of a Media Player for HDAnywhere MHUB."""

    def __init__(self, ip_address, output_id, entity_name, available_inputs, mhub_name, output_type):
        """Initialize the media player."""
        self._ip_address = ip_address
        self._output_id = output_id  # Unique ID for each output
        self._name = entity_name  # Assign the name based on the zone label
        self._state = STATE_OFF
        self._source = None
        self.base_url = f"http://{self._ip_address}/api"
        self._mhub_name = mhub_name  # Assign the mhub_name passed in the constructor
        self._output_type = output_type  # e.g., 'hdmi' or 'hdbaset'
        
        # Store available inputs dynamically
        self._available_sources = {str(k): f"{v}" for k, v in available_inputs.items()}

    @property
    def name(self):
        """Return the name of the media player."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the media player."""
        # Combine MHUB name, IP address, and output ID to form a unique identifier
        return f"{self._mhub_name}_{self._ip_address}_{self._output_id}".replace(" ", "_")

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
        url = f"{self.base_url}/power/1/"
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
        url = f"{self.base_url}/power/0/"
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
        # Find the input port corresponding to the selected source
        input_port = {v: k for k, v in self._available_sources.items()}.get(source)
        
        if input_port:
            url = f"{self.base_url}/control/switch/{self._output_id.lower()}/{input_port}/"
            _LOGGER.debug(f"Switching output {self._output_id} to input {input_port} using URL: {url}")

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    _LOGGER.info(f"Input switched to {source}.")
                    self._source = source
                    self.update()
                else:
                    _LOGGER.error(f"Failed to switch input: {response.status_code}. Response: {response.text}")
            except Exception as e:
                _LOGGER.error(f"Error switching input: {e}")
        else:
            _LOGGER.error(f"Invalid source selected: {source}. Available sources: {self._available_sources}")


    def update(self):
        """Fetch the latest state of the media player from the device."""
        url = f"{self.base_url}/data/0/"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self._state = STATE_ON if data['data']['power'] else STATE_OFF
                _LOGGER.info(f"Device state updated: {'on' if self._state == STATE_ON else 'off'}")
            else:
                _LOGGER.error(f"Failed to update device state: {response.status_code}")
        except Exception as e:
            _LOGGER.error(f"Error updating device state: {e}")
