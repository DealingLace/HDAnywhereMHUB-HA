# HDAnywhere MHUB Home Assistant Integration

This custom Home Assistant integration provides support for controlling HDAnywhere MHUB devices as media players. With this integration, you can control the power, switch inputs, and monitor the state of your MHUB's video output ports from within Home Assistant.

## Features

- **Control MHUB Outputs**: Each output is represented as a media player entity in Home Assistant.
- **Power Control**: Turn MHUB on or off from the Home Assistant interface.
- **Source Selection**: Change the video input source for each output.
- **State Monitoring**: Monitor the state of the MHUB (on/off).
- **Unique Entity IDs**: Automatically assigns unique IDs for each MHUB output entity..

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

Each media player entity is named based on the MHUB device name and the output port (e.g., MHUB U (4x3+1) A, MHUB U (4x3+1) B).

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
- Media Player Features: Each media player entity supports turning the output on/off and selecting video input sources.

## Future Enhancements

- Implementing more error handling and feedback when API requests fail.
- HACS integration and graphical setup screen
- Discovery of MHUB devices on network with auto-configure
- Control for stacked MHUB Systems
- Adding IR and CEC control for existing control packs.
- Adding passthrough control for IR and CEC for custom codes
- Cross-integration with SmartIR, for controlling other IR enabled devices via passthrough.
- Cross-integration with Universal Remote, for controlling source and output devices.

## Troubleshooting

### If the media player entities do not show up, ensure that:
   - You have restarted Home Assistant after configuring the integration.
   - The correct IP address is configured in the configuration.yaml file.
   - Enable debug logging and check the Home Assistant logs for detailed information if issues arise.
