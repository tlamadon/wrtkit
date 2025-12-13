# WRTKit

A Python library for managing OpenWRT configuration over SSH using UCI (Unified Configuration Interface).

## Features

- **Declarative Configuration**: Define OpenWRT configurations using Python objects with a simple builder pattern
- **Remote Management**: Connect to OpenWRT devices over SSH
- **Configuration Diff**: Compare local configuration with remote device configuration
- **Safe Apply**: Review changes before applying them to remote devices
- **Type Safety**: Strongly typed configuration objects for better IDE support

## Installation

```bash
pip install wrtkit
```

## Quick Start

```python
from wrtkit import UCIConfig, Network, Wireless, DHCP, Firewall
from wrtkit import SSHConnection

# Define your configuration
config = UCIConfig()

# Configure network
lan_bridge = config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("lan2") \
    .add_port("lan3")

lan = config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.10.1") \
    .netmask("255.255.255.0")

wan = config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")

# Configure DHCP
dhcp_lan = config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")

# Configure wireless
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)

config.wireless.wifi_iface("ap_two") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("my-network") \
    .encryption("psk2") \
    .key("your-password")

# Connect to remote device
ssh = SSHConnection("192.168.1.1", username="root", password="your-password")

# Compare with remote configuration
diff = config.diff(ssh)
print(diff)

# Apply configuration if satisfied
if input("Apply changes? (y/n): ") == "y":
    config.apply(ssh)
```

## Supported UCI Components

Currently supported UCI packages and options:

### Network
- **Devices**: bridges, VLANs (8021q)
- **Interfaces**: static, DHCP, batman-adv, batman-adv hardif

### Wireless
- **Radios**: channel, htmode, country, txpower
- **Interfaces**: AP, mesh, station modes
- **Features**: 802.11r fast roaming, WPA2/WPA3 encryption

### DHCP
- DHCP server configuration
- IP range, lease time, interface binding

### Firewall
- Zones (input/output/forward policies)
- Forwarding rules
- Masquerading and MTU fix

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
