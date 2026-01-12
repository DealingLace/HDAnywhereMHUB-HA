# HDAnywhere MHUB Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/DealingLace/HDAnywhereMHUB-HA.svg)](https://github.com/DealingLace/HDAnywhereMHUB-HA/releases)

A modern, fully async Home Assistant integration for controlling HDAnywhere MHUB matrix switchers (API v2.1+).

## ✨ What's New in v2.0

This is a **complete rewrite** with production-ready features:

- 🚀 **Fully Async** - Non-blocking I/O operations for optimal Home Assistant performance
- 🔄 **Efficient Polling** - Single coordinator manages all entities, reducing network traffic
- 🎯 **UI Configuration** - Beautiful config flow with automatic device discovery
- 🔍 **Zeroconf Discovery** - Automatically finds MHUB devices on your network
- 🛡️ **Robust Error Handling** - Automatic retries with exponential backoff
- 📊 **Diagnostics Support** - Easy troubleshooting with downloadable diagnostics
- 🎨 **Device Registry** - All entities grouped under a single device
- ⚙️ **Custom Services** - Advanced control beyond the UI
- 🌐 **Internationalization** - Translation-ready with full i18n support
- 📝 **Type Hints** - Fully typed for better IDE support and maintainability

## 🔧 Requirements

- Home Assistant 2023.1.0 or newer
- HDAnywhere MHUB with API v2.1 or later
- MHUB device accessible on your local network

> **Note:** For API v2.0 compatibility, use the [api_v2.0 branch](https://github.com/DealingLace/HDAnywhereMHUB-HA/tree/api_v2.0)

## 📥 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/DealingLace/HDAnywhereMHUB-HA`
5. Select category: "Integration"
6. Click "Add"
7. Find "HDAnywhere MHUB" in HACS and click "Download"
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/DealingLace/HDAnywhereMHUB-HA/releases)
2. Extract the `hdanywheremhub` folder to `custom_components/` in your Home Assistant configuration directory
3. Restart Home Assistant

## ⚙️ Configuration

### UI Setup (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "HDAnywhere MHUB"
4. Enter your MHUB's IP address
5. Click **Submit**

The integration will automatically:
- Connect to your MHUB device
- Fetch device information
- Create media player entities for each configured zone
- Create a switch entity for power control

### Automatic Discovery

If your MHUB supports zeroconf/mDNS, it will be automatically discovered:

1. Go to **Settings** → **Devices & Services**
2. Look for a discovered "HDAnywhere MHUB" device
3. Click **Configure**
4. Confirm the device

### Legacy YAML Configuration (Deprecated)

> ⚠️ YAML configuration is deprecated and will be removed in a future version. Please migrate to UI configuration.

```yaml
# Remove this from configuration.yaml and use UI setup instead
media_player:
  - platform: hdanywheremhub
    ip_address: 192.168.1.100

switch:
  - platform: hdanywheremhub
    ip_address: 192.168.1.100
```

## 🎮 Features

### Media Player Entities

Each zone output becomes a media player entity with:

- **Power Control** - Turn the entire MHUB on/off
- **Source Selection** - Switch between available inputs
- **State Monitoring** - Real-time power state updates
- **Zone Information** - Displays zone name, output type (HDMI/HDBaseT), and configuration

**Entity Naming Format:** `media_player.[zone_name]_[output_id]_[type]`

Example: `media_player.living_room_b_hdbaset`

### Switch Entity

A single switch entity for simple on/off control of the entire device:

- `switch.[device_name]_power`

### Device Information

All entities are grouped under a single MHUB device showing:

- Device name
- Firmware version
- Hardware version
- Serial number
- Configuration URL (click to open device web interface)

### Extra State Attributes

Each media player provides additional attributes:

- `output_id` - Output port identifier
- `output_type` - Connection type (hdmi/hdbaset)
- `zone_label` - Zone name from device
- `arc_input` - ARC input configuration
- `auto_switch_mode` - Automatic switching status
- `mhub_name` - Device name

## 🔧 Advanced Features

### Custom Services

#### `hdanywheremhub.switch_output`

Directly switch any output to any input without using the UI:

```yaml
service: hdanywheremhub.switch_output
data:
  target_output: "a"
  target_input: "3"
```

#### `hdanywheremhub.refresh_sources`

Force refresh of input sources and zone configuration:

```yaml
service: hdanywheremhub.refresh_sources
```

Use this after reconfiguring zones or inputs on the MHUB device.

### Configuration Options

Click **Configure** on your MHUB device in the UI to adjust:

- **Update Interval** - How often to poll the device (5-300 seconds, default: 10)

### Diagnostics

To download diagnostic information for troubleshooting:

1. Go to **Settings** → **Devices & Services**
2. Click on your MHUB device
3. Click the three dots menu
4. Select **Download diagnostics**

This provides a JSON file with device state, configuration, and system information (no sensitive data included).

## 🏗️ Architecture

### Modern Design Patterns

- **Async API Client** - Non-blocking HTTP requests with aiohttp
- **Data Coordinator** - Single polling cycle shared by all entities
- **Config Flow** - User-friendly UI setup with validation
- **Type Hints** - Full type annotations throughout
- **Exception Handling** - Granular exception types with automatic recovery
- **Connection Pooling** - Efficient resource usage
- **Exponential Backoff** - Smart retry logic for reliability

### Performance Optimizations

- **Cached Static Data** - System info and zone data cached to reduce API calls
- **Shared Sessions** - Single HTTP session reused across requests
- **Efficient Updates** - Only device state polled regularly, configuration cached
- **Immediate Refresh** - Commands trigger instant coordinator update

## 🐛 Troubleshooting

### Entities Not Appearing

1. Verify MHUB API version is 2.1+ (check device web interface)
2. Ensure zones are configured on the MHUB device
3. Check Home Assistant logs for errors
4. Try removing and re-adding the integration

### Connection Issues

1. Verify IP address is correct
2. Ensure MHUB is powered on and accessible
3. Check firewall settings
4. Test connection: `curl http://[MHUB_IP]/api/data/0`

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.hdanywheremhub: debug
```

Then check Home Assistant logs for detailed information.

### Download Diagnostics

Use the diagnostics feature (see above) to gather information for bug reports.

## 🤝 Integration with Universal Media Player

Home Assistant's [Universal Media Player](https://www.home-assistant.io/integrations/universal/) allows combining MHUB outputs with your endpoint devices:

```yaml
media_player:
  - platform: universal
    name: Living Room Entertainment
    children:
      - media_player.living_room_b_hdbaset
      - media_player.living_room_tv
      - media_player.living_room_receiver
    commands:
      turn_on:
        service: media_player.turn_on
        target:
          entity_id: media_player.living_room_b_hdbaset
      turn_off:
        service: media_player.turn_off
        target:
          entity_id: media_player.living_room_b_hdbaset
```

Combine with:
- [Universal Remote](https://www.home-assistant.io/integrations/remote/) for comprehensive control
- [SmartIR](https://github.com/smartHomeHub/SmartIR) for IR device control
- Automations to create scenes and multi-device control

## 📋 Known Limitations

- **No Per-Output State** - API doesn't provide which input is active on each output
- **Global Power** - Power control affects the entire matrix, not individual outputs
- **Polling Delay** - State updates may take up to the configured scan interval (default: 10s)
- **Single Device** - Currently supports one MHUB device per integration instance

## 🛣️ Roadmap

Future enhancements planned:

- [ ] PyPI library for MHUB API (for easier maintenance and testing)
- [ ] Support for stacked MHUB systems
- [ ] Audio matrix control
- [ ] IR and CEC control integration
- [ ] Custom code pass-through for IR/CEC
- [ ] Per-zone source filtering (like uControl)
- [ ] Local source state tracking
- [ ] API v2.0 auto-detection and compatibility mode

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request

For bugs, please include:
- Home Assistant version
- Integration version
- MHUB firmware version
- Diagnostic data (if possible)
- Steps to reproduce

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- HDAnywhere for the MHUB API documentation
- Home Assistant community for integration guidelines
- All contributors and users providing feedback

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/DealingLace/HDAnywhereMHUB-HA/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DealingLace/HDAnywhereMHUB-HA/discussions)
- **Documentation**: This README and code docstrings

---

**Made with ❤️ for the Home Assistant community**
