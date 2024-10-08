"""HDAnywhere MHUB Integration."""
from homeassistant.core import HomeAssistant
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "hdanywheremhub"

def setup(hass: HomeAssistant, config: dict):
    """Set up the hdanywheremhub component."""
    _LOGGER.info("HDAnywhere MHUB component is set up!")
    return True
