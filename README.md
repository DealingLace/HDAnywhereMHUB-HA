# HDAnywhere MHUB Home Assistant Integration

This custom Home Assistant integration provides support for controlling HDAnywhere MHUB devices (API 2.1+) as media players. With this integration, you can monitor and control the power, as well as switch available inputs to available outputs from within Home Assistant.

## Features

- **Control MHUB Outputs**: Each output is represented as a media player entity in Home Assistant.
- **Power Control**: Turn MHUB on or off from the media player entity in the Home Assistant dashboard.
- **Source Selection**: Change the video input source for each output.
- **State Monitoring**: Monitor the state of the MHUB (on/off).
- **Unique Entity IDs**: Automatically assigns unique IDs for each MHUB output entity.

## Installation

### Manual Installation

1. **Download the Repository**:
   - Download and extract the contents of this repository.

2. **Move Files**:
   - Copy the `hdanywheremhub` folder to your Home Assistant configuration's `custom_components` directory.
   - If this directory does not exist, create it.

## Configuration

To set up the integration, you need to configure it through the configuration.yaml file. Add the following configuration under the media_player domain:

```
media_player:
  - platform: hdanywheremhub
    ip_address: 192.168.1.100  # Replace with your MHUB's IP address
```

#### Restart Home Assistant

Once the configuration is added, restart Home Assistant to load the integration.

## Features and Capabilities

### 1. Power Control

The media player entities created by this integration allow you to turn the MHUB outputs on and off. You can control power using Home Assistant's media player controls.

### 2. Input Source Selection

You can switch between available input sources using the source feature. The available sources are dynamically fetched from the MHUB device and displayed in Home Assistant.

### 3. Entity Names

Each media player entity is named based on the MHUB device name and the output port.

- Note that the device name is not the component name from the manufacturer, rather what was assigned to it during setup (eg. House CoolGuy A, House CoolGuy B)

### 4. Unique Entity IDs

The integration automatically assigns a unique entity ID for each output based on the MHUB name, the output ID (like A, B, C), and the IP address. This ensures persistent tracking across Home Assistant restarts.

## Logging

The integration logs detailed information that can be useful for debugging. You can enable debug logging in Home Assistant by adding the following configuration to your configuration.yaml:

```
logger:
  default: warning
  logs:
    custom_components.hdanywheremhub: debug
```

## How It Works

- Platform Initialization: On setup, the integration makes an API request to the MHUB device to fetch the list of video input and output ports.
- Entity Creation: For each output port, a media player entity is created in Home Assistant. Each entity is assigned a unique name and ID based on the MHUB name and the output ID.
- Media Player Features: Each media player entity supports turning the matrix on/off and selecting video input sources for each output.

## Known Limitations

- When the device is turned on or off, an API call is made to ensure the trigger was performed successfully, however, the MHUB does not immediately report that it is on, like it does when you turn it off. Therefore, since the integration never assumes the state of the device, there is a delay on an "on" request, as it will only report it's true state when available.

## Future Enhancements

- Refactoring API calls into a PyPI library to fit HA guidelines
- Implementing more error handling and feedback when API requests fail.
- HACS integration and graphical setup screen
- Discovery of MHUB devices on network with auto-configure
- Control for stacked MHUB Systems
- Adding IR and CEC control for existing control packs.
- Adding passthrough control for IR and CEC for custom codes
- Cross-integration with SmartIR, for controlling other IR enabled devices via passthrough.
- Cross-integration with Universal Remote, for controlling source and output devices.
- Backwards compatibility with API v2.0, for older hardware

## Troubleshooting

### First place to start
   - Ensure the MHUB is compatible with MHUB API v2.1

### If the media player entities do not show up, ensure that:
   - You have restarted Home Assistant after configuring the integration.
   - The correct IP address is configured in the configuration.yaml file.
   - Enable debug logging and check the Home Assistant logs for detailed information if issues arise.
