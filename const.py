"""Constants for the HDAnywhere MHUB integration."""
from datetime import timedelta
from typing import Final

# Integration domain
DOMAIN: Final = "hdanywheremhub"

# Configuration and options
CONF_API_VERSION: Final = "api_version"

# Default values
DEFAULT_NAME: Final = "HDAnywhere MHUB"
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=10)
DEFAULT_TIMEOUT: Final = 10
DEFAULT_API_VERSION: Final = "2.1"

# API endpoints
API_BASE_PATH: Final = "/api"
API_ENDPOINT_SYSTEM_INFO: Final = "/data/100"
API_ENDPOINT_ZONE_DATA: Final = "/data/102"
API_ENDPOINT_DEVICE_STATE: Final = "/data/0"
API_ENDPOINT_POWER: Final = "/power"
API_ENDPOINT_SWITCH: Final = "/control/switch"

# API versions
API_VERSION_2_0: Final = "2.0"
API_VERSION_2_1: Final = "2.1"
SUPPORTED_API_VERSIONS: Final = [API_VERSION_2_0, API_VERSION_2_1]

# Device information
MANUFACTURER: Final = "HDAnywhere"
MODEL: Final = "MHUB"

# Output types
OUTPUT_TYPE_HDMI: Final = "hdmi"
OUTPUT_TYPE_HDBASET: Final = "hdbaset"

# Attributes
ATTR_OUTPUT_ID: Final = "output_id"
ATTR_OUTPUT_TYPE: Final = "output_type"
ATTR_ZONE_LABEL: Final = "zone_label"
ATTR_ARC_INPUT: Final = "arc_input"
ATTR_AUTO_SWITCH_MODE: Final = "auto_switch_mode"
ATTR_INPUT_ID: Final = "input_id"
ATTR_MHUB_NAME: Final = "mhub_name"
ATTR_FIRMWARE_VERSION: Final = "firmware_version"
ATTR_HARDWARE_VERSION: Final = "hardware_version"
ATTR_SERIAL_NUMBER: Final = "serial_number"

# Service names
SERVICE_SWITCH_OUTPUT: Final = "switch_output"
SERVICE_REFRESH_SOURCES: Final = "refresh_sources"

# Service schema attributes
ATTR_TARGET_OUTPUT: Final = "target_output"
ATTR_TARGET_INPUT: Final = "target_input"

# Update coordinator
UPDATE_LISTENER: Final = "update_listener"
COORDINATOR: Final = "coordinator"
MHUB_CLIENT: Final = "mhub_client"
UNDO_UPDATE_LISTENER: Final = "undo_update_listener"

# Platforms
PLATFORMS: Final = ["media_player", "switch"]

# Error messages
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_INVALID_API_VERSION: Final = "invalid_api_version"
ERROR_TIMEOUT: Final = "timeout"
ERROR_UNKNOWN: Final = "unknown"
ERROR_ALREADY_CONFIGURED: Final = "already_configured"

# Retry configuration
MAX_RETRIES: Final = 3
RETRY_DELAY: Final = 1  # seconds
BACKOFF_MULTIPLIER: Final = 2

# Connection limits
MAX_CONNECTIONS: Final = 10
CONNECTION_TIMEOUT: Final = 30

# Zeroconf
ZEROCONF_TYPE_HTTP: Final = "_http._tcp.local."
ZEROCONF_TYPE_HDA: Final = "_hda._tcp.local."
ZEROCONF_NAME: Final = "MHUB"
