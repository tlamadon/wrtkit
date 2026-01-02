# WRTKit

A Python library for managing OpenWRT configuration over SSH and serial console using UCI (Unified Configuration Interface).

## Features

- **Command Line Interface**: Manage devices directly from your terminal with `wrtkit preview` and `wrtkit apply`
- **Fleet Mode**: Manage multiple devices with coordinated atomic updates and two-phase execution
- **Testing Mode**: Run network diagnostics (ping, iperf) between devices defined in your fleet
- **Composable Configuration**: Define OpenWRT configurations using type-safe Pydantic models with immutable builder patterns
- **YAML/JSON Support**: Load and save configurations in YAML or JSON format
  - Generate JSON/YAML schemas for IDE autocomplete and validation
  - Permissive schema accepts custom UCI options
  - Serialize and deserialize individual sections or complete configs
- **Multiple Connection Types**:
  - SSH connections (via paramiko)
  - Serial console connections (via pyserial) - works with picocom, minicom, etc.
- **Enhanced Configuration Diff**: Compare local configuration with remote device configuration
  - Track remote-only UCI settings (not managed by your config)
  - Tree-structured diff output grouped by package and resource
  - Linear format for quick review
  - Colored terminal output
  - Common settings tracking
- **Safe Apply**: Review changes before applying them to remote devices
- **Type Safety**: Pydantic-based models for validation, serialization, and excellent IDE support

## Installation

```bash
pip install wrtkit
```

## Command Line Interface

WRTKit includes a CLI for managing devices directly from your terminal.

### Quick CLI Examples

```bash
# Validate a configuration file
wrtkit validate config.yaml

# Preview changes (compare config with device)
wrtkit preview config.yaml 192.168.1.1

# Preview with UCI commands shown
wrtkit preview config.yaml router.local --show-commands

# Apply changes (dry-run first)
wrtkit apply config.yaml 192.168.1.1 --dry-run

# Apply changes for real
wrtkit apply config.yaml 192.168.1.1 -p mypassword

# Apply without confirmation prompt
wrtkit apply config.yaml 192.168.1.1 -y

# Show all UCI commands from a config
wrtkit commands config.yaml

# Import config from a device
wrtkit import 192.168.1.1 router-backup.yaml
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `wrtkit preview` | Compare config with device, show diff |
| `wrtkit apply` | Apply configuration to device |
| `wrtkit validate` | Validate config file without connecting |
| `wrtkit commands` | Output UCI commands as shell script |
| `wrtkit import` | Import config from device and save as YAML/JSON |
| `wrtkit fleet` | Manage multiple devices with coordinated updates |
| `wrtkit testing` | Run network tests (ping, iperf) between devices |

For full CLI documentation, see [Command Line Interface](guide/cli.md).

### Environment Variables

Create a `.env` file for credentials (loaded automatically):

```bash
# .env
WRTKIT_TARGET=192.168.1.1
WRTKIT_PASSWORD=mysecretpassword
WRTKIT_KEY_FILE=/path/to/ssh/key
WRTKIT_TIMEOUT=60
```

You can also use environment variables in your YAML configs with OmegaConf interpolation:

```yaml
# config.yaml
wireless:
  interfaces:
    wlan0:
      ssid: MyNetwork
      key: ${oc.env:WIFI_PASSWORD}
```

!!! tip "Security"
    Sensitive fields like `key`, `password`, and `sae_password` are automatically masked in CLI output, showing only the first 3 characters (e.g., `myp*******`).

## Example YAML Configuration

```yaml
network:
  devices:
    br_lan:
      name: br-lan
      type: bridge
      ports:
        - lan1
        - lan2
  interfaces:
    lan:
      device: br-lan
      proto: static
      ipaddr: 192.168.1.1
      netmask: 255.255.255.0

wireless:
  radios:
    radio0:
      channel: 36
      htmode: HE80
      country: US
  interfaces:
    default_radio0:
      device: radio0
      mode: ap
      network: lan
      ssid: MyNetwork
      encryption: sae
      key: SecurePassword123!

dhcp:
  sections:
    lan:
      interface: lan
      start: 100
      limit: 150
      leasetime: 12h
```

## Target Formats

The CLI supports multiple formats for specifying the device to connect to:

### SSH Connections

| Format | Example | Description |
|--------|---------|-------------|
| IP address | `192.168.1.1` | Connect via SSH to IP |
| Hostname | `router.local` | Connect via SSH to hostname |
| IP:port | `192.168.1.1:2222` | Connect via SSH on custom port |
| user@host | `root@192.168.1.1` | Connect with specific username |
| user@host:port | `admin@router.local:2222` | Full SSH connection string |

### Serial Connections

| Format | Example | Description |
|--------|---------|-------------|
| Linux serial | `/dev/ttyUSB0` | Serial port on Linux |
| macOS serial | `/dev/tty.usbserial` | Serial port on macOS |
| Windows serial | `COM3` | Serial port on Windows |

## Next Steps

- [Command Line Interface](guide/cli.md) - Full CLI documentation
- [Fleet Mode](guide/fleet.md) - Manage multiple devices
- [Testing Mode](guide/testing.md) - Network diagnostics (ping, iperf)
- [YAML/JSON Configuration](yaml-json-guide.md) - Configuration file format
- [Quick Start Tutorial](getting-started/quick-start.md) - Get started quickly
- [API Reference](api/config.md) - Python API documentation
- [Examples](examples/basic-router.md) - Example configurations

## License

WRTKit is released under the [MIT License](https://github.com/tlamadon/wrtkit/blob/main/LICENSE).
