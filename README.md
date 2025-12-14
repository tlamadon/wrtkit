# WRTKit

A Python library for managing OpenWRT configuration over SSH and serial console using UCI (Unified Configuration Interface).

## Features

- **Composable Configuration**: Define OpenWRT configurations using type-safe Pydantic models with immutable builder patterns
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

## Quick Start

```python
from wrtkit import UCIConfig
from wrtkit.network import NetworkInterface, NetworkDevice
from wrtkit.wireless import WirelessRadio, WirelessInterface
from wrtkit.dhcp import DHCPSection
from wrtkit import SSHConnection

# Create configuration
config = UCIConfig()

# Configure network - Constructor style
lan = NetworkInterface(
    "lan",
    device="br-lan",
    proto="static",
    ipaddr="192.168.10.1",
    netmask="255.255.255.0"
)
config.network.add_interface(lan)

# Configure network - Builder style (immutable, composable)
wan = NetworkInterface("wan")\
    .with_device("eth1")\
    .with_dhcp()
config.network.add_interface(wan)

# Create a bridge device
bridge = NetworkDevice("br_lan")\
    .with_name("br-lan")\
    .with_type("bridge")\
    .with_port("lan1")\
    .with_port("lan2")\
    .with_port("lan3")
config.network.add_device(bridge)

# Configure DHCP
dhcp = DHCPSection("lan")\
    .with_interface("lan")\
    .with_range(100, 150, "12h")
config.dhcp.add_dhcp(dhcp)

# Configure wireless - Mix constructor and builder
radio = WirelessRadio("radio0", channel=11, htmode="HT20")\
    .with_country("US")\
    .with_disabled(False)
config.wireless.add_radio(radio)

ap = WirelessInterface("ap_two")\
    .with_device("radio0")\
    .with_ap("my-network", "psk2", "your-password")\
    .with_network("lan")
config.wireless.add_interface(ap)

# Connect to remote device via SSH
ssh = SSHConnection("192.168.1.1", username="root", password="your-password")

# Compare with remote configuration
diff = config.diff(ssh)
print(diff.to_tree())

# Apply configuration if satisfied
if input("Apply changes? (y/n): ") == "y":
    config.apply(ssh)
```

## Composable Builder Pattern

WRTKit uses Pydantic models with immutable builder methods for maximum composability:

### Three Ways to Configure

```python
from wrtkit.network import NetworkInterface

# 1. Constructor with all arguments
lan = NetworkInterface(
    "lan",
    device="br-lan",
    proto="static",
    ipaddr="192.168.1.1",
    netmask="255.255.255.0"
)

# 2. Immutable builder pattern
lan = NetworkInterface("lan")\
    .with_device("br-lan")\
    .with_static_ip("192.168.1.1")

# 3. Mix both approaches
lan = NetworkInterface("lan", device="br-lan")\
    .with_static_ip("192.168.1.1")
```

### Reusable Configurations

The immutable builder pattern enables powerful composition:

```python
# Create a base configuration template
base_static = NetworkInterface("template")\
    .with_proto("static")\
    .with_netmask("255.255.255.0")

# Compose variations - each is a new independent copy
lan = NetworkInterface("lan")\
    .with_device("br-lan")\
    .with_static_ip("192.168.1.1")

guest = NetworkInterface("guest")\
    .with_device("br-guest")\
    .with_static_ip("192.168.100.1")

iot = NetworkInterface("iot")\
    .with_device("br-iot")\
    .with_static_ip("192.168.200.1")

# Add them all to config
for interface in [lan, guest, iot]:
    config.network.add_interface(interface)
```

### Dict-Based Configuration

Pydantic models support dict unpacking for config-driven setups:

```python
# Load from config file, environment, etc.
interface_configs = [
    {"name": "lan", "device": "br-lan", "proto": "static", "ipaddr": "192.168.1.1"},
    {"name": "guest", "device": "br-guest", "proto": "static", "ipaddr": "192.168.100.1"},
]

for cfg in interface_configs:
    name = cfg.pop("name")
    iface = NetworkInterface(name, **cfg)
    config.network.add_interface(iface)
```

## Connection Types

### SSH Connection

```python
from wrtkit import SSHConnection

# Basic SSH connection
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    password="your-password"
)

# SSH with key authentication
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    key_filename="/path/to/private_key"
)

# Use as context manager
with SSHConnection("192.168.1.1", username="root", password="pass") as ssh:
    diff = config.diff(ssh)
    config.apply(ssh)
```

### Serial Console Connection

Perfect for devices without network access or when SSH is unavailable:

```python
from wrtkit import SerialConnection

# Basic serial connection
serial = SerialConnection(
    port="/dev/ttyUSB0",     # Linux: /dev/ttyUSB0, macOS: /dev/tty.usbserial-*, Windows: COM3
    baudrate=115200,          # Most OpenWRT devices use 115200
    timeout=5.0
)

# Serial with login credentials (if needed)
serial = SerialConnection(
    port="/dev/ttyUSB0",
    baudrate=115200,
    login_username="root",
    login_password="your-password"
)

# Use exactly like SSH!
with serial:
    diff = config.diff(serial)
    if not diff.is_empty():
        print(diff.to_tree())
        config.apply(serial)
```

**Serial Connection Tips:**
- Make sure you have permission to access the serial port (add user to `dialout` group on Linux)
- Close other programs using the port (like picocom or minicom)
- Common baudrates: 9600, 19200, 38400, 57600, 115200
- See [examples/serial_example.py](examples/serial_example.py) for a complete example

## Configuration Diff

WRTKit provides powerful diff capabilities to compare your local configuration with what's actually running on the remote device.

### Basic Diff

```python
# Compare configurations
diff = config.diff(ssh)

# Linear format (default, with colors and summary)
print(str(diff))
# Output: Configuration differences: +5 to add, ~2 to modify, *10 remote-only

# Tree-structured format (grouped by package and resource, with colors and summary)
print(diff.to_tree())

# Disable colors if needed (e.g., for piping to files)
print(diff.to_string(color=False))
print(diff.to_tree(color=False))
```

Both formats include a helpful summary header showing the count of each type of change.

### Understanding Diff Output

The diff engine tracks four types of changes, each with a distinct color in terminal output:

- **<span style="color:green">`+`</span> (Add)** - **Green**: Settings defined in your local config but missing on the remote device
- **<span style="color:red">`-`</span> (Remove)** - **Red**: Settings on the remote device that should be removed (deprecated - see remote-only below)
- **<span style="color:yellow">`~`</span> (Modify)** - **Yellow**: Settings that exist in both but have different values
- **<span style="color:cyan">`*`</span> (Remote-only)** - **Cyan**: Settings on the remote device that aren't managed by your local config

Colors are enabled by default in terminal output and can be disabled with the `color=False` parameter.

### Remote-Only Settings

By default, the diff tracks UCI settings that exist on the remote device but aren't mentioned in your local configuration. This is useful for:

- Discovering existing configurations you might want to manage
- Identifying settings managed by other tools or manually
- Understanding the complete state of your device

```python
# Track remote-only settings (default)
diff = config.diff(ssh, show_remote_only=True)

# Or treat them as settings to remove (old behavior)
diff = config.diff(ssh, show_remote_only=False)
```

### Tree-Structured Output

The tree format organizes changes hierarchically by package and section:

```
network/
├── lan
│     + ipaddr = 192.168.1.1
│     + netmask = 255.255.255.0
│     ~ proto
│       - static
│       + dhcp
└── guest
      * proto = dhcp (remote-only)
      * ipaddr = 192.168.2.1 (remote-only)

wireless/
└── radio0
      + channel = 11
      ~ htmode
        - HT40
        + HT20
```

This makes it easy to see:
- Which packages have changes
- Which resources within each package are affected
- What specific options are being added, modified, or exist remotely

### Example

See [examples/diff_demo.py](examples/diff_demo.py) for a complete demonstration of the diff functionality.

## Supported UCI Components

Currently supported UCI packages and options:

### Network
- **Devices**: bridges, VLANs (8021q)
- **Interfaces**: static, DHCP, batman-adv, batman-adv hardif
- **Methods**: `.with_device()`, `.with_proto()`, `.with_static_ip()`, `.with_dhcp()`, `.with_mtu()`, etc.

### Wireless
- **Radios**: channel, htmode, country, txpower
- **Interfaces**: AP, mesh, station modes
- **Features**: 802.11r fast roaming, WPA2/WPA3 encryption
- **Methods**: `.with_channel()`, `.with_ssid()`, `.with_ap()`, `.with_mesh()`, `.with_encryption()`, etc.

### DHCP
- DHCP server configuration
- IP range, lease time, interface binding
- **Methods**: `.with_interface()`, `.with_range()`, `.with_leasetime()`, etc.

### Firewall
- Zones (input/output/forward policies)
- Forwarding rules
- Masquerading and MTU fix
- **Methods**: `.with_name()`, `.with_input()`, `.with_network()`, `.with_masq()`, etc.

## Type Safety and Validation

All configuration objects are Pydantic models, providing:

- **Type validation**: Catch errors before applying to devices
- **IDE autocomplete**: Full IntelliSense support
- **Serialization**: Export to JSON, YAML, dict
- **Documentation**: Self-documenting with docstrings

```python
# Type validation catches errors
interface = NetworkInterface("lan", mtu="invalid")  # ValidationError: value is not a valid integer

# Serialize to dict/JSON
config_dict = lan.model_dump()
config_json = lan.model_dump_json()

# Load from dict/JSON
lan_copy = NetworkInterface.model_validate(config_dict)
```

## Examples

Check out the [examples](examples/) directory for:
- [simple_example.py](examples/simple_example.py) - Basic router setup
- [router_config.py](examples/router_config.py) - Advanced mesh network configuration

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
black src/ tests/ examples/
ruff check src/ tests/ examples/
mypy src/wrtkit
```

## Publishing to PyPI

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions on how to publish this package to PyPI.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
