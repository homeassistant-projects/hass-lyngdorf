# Lyngdorf A/V Control for Home Assistant

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
![release_badge](https://img.shields.io/github/v/release/homeassistant-projects/hass-lyngdorf.svg)
![release_date](https://img.shields.io/github/release-date/homeassistant-projects/hass-lyngdorf.svg)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/MIT)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/DYks67r)
[![Support on Patreon][patreon-shield]][patreon]

![Lyngdorf Logo](https://github.com/homeassistant-projects/hass-lyngdorf/blob/main/brands/logo.png?raw=true)

Control your Lyngdorf audio/video processor from Home Assistant via RS232 or IP connection.

## Status

**Implemented and ready for use!** This integration supports Lyngdorf MP-50 and MP-60 processors. Hardware testing and feedback welcome.

## Features

### Media Player Controls
- Full media player control (power, volume, mute, source selection)
- Custom source naming via UI configuration
- Zone 2 support with independent control
- Dynamic source discovery

### Audio Processing
- **RoomPerfect Controls** - Select entities for focus positions and voicings
- **Audio Mode Selection** - Choose processing modes via select entity
- **Channel Trim Controls** - Fine-tune bass, treble, center, LFE, surround, and height channels
- **Lip Sync Adjustment** - Precise delay control in milliseconds
- **Loudness Control** - Toggle loudness compensation
- **DTS Dialog Control** (MP-60 only) - Enhance dialog clarity

### Real-time State Updates
- Callback-based push notifications from device
- Efficient DataUpdateCoordinator pattern
- Immediate UI updates when device state changes

### Information Sensors
- Audio format sensor (codec, sample rate, channels)
- Video input sensor
- Video output sensor

### Connection
- RS232 serial and IP/socket connection support
- Config flow UI for easy setup
- Options flow for reconfiguration
- Volume range: -99.9 to +20.0 dB (MP-50) or +24.0 dB (MP-60)

## Supported Devices

| Model | Status | Volume | Notes |
|-------|--------|--------|-------|
| Lyngdorf MP-50 | Untested | -99.9 to +20.0 dB | Includes RoomPerfect |
| Lyngdorf MP-60 | Untested | -99.9 to +24.0 dB | Includes RoomPerfect & DTS Dialog Control |

**Note:** All models use similar RS232/IP protocols. If you can test with hardware, please report your results!

## Installation

### Step 1: Install Custom Components

Make sure that [Home Assistant Community Store (HACS)](https://github.com/custom-components/hacs) is installed and then add the 'Integration' repository: `homeassistant-projects/hass-lyngdorf`.

### Step 2: Configuration

This integration is completely configured via the Home Assistant UI using config flow:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for and select **Lyngdorf**
4. Follow the prompts to configure your device:
   - Select your Lyngdorf model (MP-50 or MP-60)
   - Enter the connection URL (e.g., `socket://192.168.1.100:84` for network, or `/dev/ttyUSB0` for serial)
   - Optionally set a custom baud rate if using RS232

No `configuration.yaml` entries are required.

## Hardware Requirements

### RS232 Connection

- **RS232 to USB adapter**: [Example cable](https://www.amazon.com/RS232-to-USB/dp/B0759HSLP1?tag=carreramfi-20)
- **Baud rate**: 115200 (default)
- **Protocol**: 8N1 (8 data bits, no parity, 1 stop bit)

### IP/Network Connection

- **Port**: 84 (default)
- Your processor must support network control
- Ensure your processor is connected to your network

## Supported Controls

| Feature | Entity Type | Main Zone | Zone 2 |
|---------|-------------|-----------|--------|
| Power On/Off | media_player | ✅ | ✅ |
| Volume Control | media_player | ✅ (dB scale) | ✅ |
| Mute | media_player | ✅ | ✅ |
| Source Selection | media_player | ✅ | ✅ |
| RoomPerfect Position | select | ✅ | - |
| RoomPerfect Voicing | select | ✅ | - |
| Audio Mode | select | ✅ | - |
| Bass Trim | number | ✅ | - |
| Treble Trim | number | ✅ | - |
| Center Trim | number | ✅ | - |
| LFE Trim | number | ✅ | - |
| Surround Trim | number | ✅ | - |
| Height Trim | number | ✅ | - |
| Lip Sync Delay | number | ✅ | - |
| Audio Format | sensor | ✅ | - |
| Video Input | sensor | ✅ | - |
| Video Output | sensor | ✅ | - |

## Source Inputs

Sources are dynamically discovered from the processor. Common inputs include:

- **HDMI** (source 1)
- **SPDIF 1-8** (sources 3-10): Optical, AES/EBU, and Coaxial digital
- **Internal Player** (source 11)
- **USB** (source 12)
- **16-Channel AES** (sources 20-23, MP-60 optional module)
- **Audio Return Channel** (source 24)

## Troubleshooting

### Connection Issues

- Verify the correct serial port or IP address
- Check that your RS232 cable is properly connected
- Ensure baud rate matches your processor settings (default: 115200)
- For IP connections, verify port 84 is accessible

### Integration Not Loading

- Check Home Assistant logs for error messages
- Verify `pylyngdorf` directory exists in HA root
- Restart Home Assistant after installation

## Support

- **Issues**: [GitHub Issues](https://github.com/homeassistant-projects/hass-lyngdorf/issues)
- **Community**: [Home Assistant Community Forum](https://community.home-assistant.io/t/lyngdorf-audio-control/450908)
- **Pull Requests**: Contributions welcome!

## Technical Details

This integration uses an embedded Python library for communication:

### pylyngdorf (Lyngdorf Control)
- Lyngdorf RS232/IP protocol implementation
- Async/await support for Home Assistant
- **Callback-based state updates** - Real-time push notifications from device
- **DataUpdateCoordinator** - Efficient state management following HA 2025 best practices
- Handles verbosity levels and echo filtering
- RoomPerfect and advanced audio controls
- Model-specific configurations (MP-50/MP-60)
- Custom exception hierarchy for robust error handling
- Dataclass-based state representation for type safety

### Architecture
- **Protocol Layer** - Handles RS232/IP communication and parses unsolicited device updates
- **Device API** - Clean, typed interface to device controls
- **Coordinator** - Manages state updates and entity refresh
- **Entity Platforms** - media_player, select, number, and sensor entities

## See Also

* [pylyngdorf library](custom_components/lyngdorf/pylyngdorf/) - Embedded Python library for Lyngdorf control
* [Lyngdorf RS232 Protocol](custom_components/lyngdorf/pylyngdorf/models.py) - Command reference
* [Example Usage](custom_components/lyngdorf/pylyngdorf/example-async.py) - Python library examples
* [fishloa/lyngdorf](https://github.com/fishloa/lyngdorf) - Alternative Lyngdorf integration




[forum]: https://forum/lyngdorf
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg
[patreon]: https://www.patreon.com/rsnodgrass
[patreon-shield]: https://frenck.dev/wp-content/uploads/2019/12/patreon.png
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
