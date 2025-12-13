# WRTKit Documentation

**WRTKit** is a Python library for managing OpenWRT configuration over SSH using UCI (Unified Configuration Interface).

## Features

:material-language-python: **Pythonic API**
:   Define OpenWRT configurations using Python with a fluent builder pattern

:material-network: **SSH Integration**
:   Connect to and manage remote OpenWRT devices over SSH

:material-compare: **Configuration Diff**
:   Compare local configuration with remote device state

:material-check-all: **Safe Apply**
:   Review changes before applying them to devices

:material-file-code: **Script Export**
:   Generate standalone shell scripts for manual deployment

## Quick Example

```python
from wrtkit import UCIConfig, SSHConnection

# Define your configuration
config = UCIConfig()

config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("MyPassword")

# Apply to remote device
with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
    diff = config.diff(ssh)
    if not diff.is_empty():
        config.apply(ssh)
```

## Installation

```bash
pip install wrtkit
```

## Supported Components

### Network Configuration
- Network devices (bridges, VLANs)
- Network interfaces (static IP, DHCP client)
- BATMAN-ADV mesh networking
- MTU, gateway, and routing configuration

### Wireless Configuration
- Radio configuration (channel, power, country)
- WiFi interfaces (AP, mesh, station modes)
- WPA2/WPA3 encryption
- 802.11r fast roaming

### DHCP Configuration
- DHCP server settings
- IP address ranges
- Lease time configuration

### Firewall Configuration
- Firewall zones
- Traffic policies (input/output/forward)
- Forwarding rules
- NAT/masquerading

## Next Steps

- [Installation Guide](getting-started/installation.md)
- [Quick Start Tutorial](getting-started/quick-start.md)
- [API Reference](api/config.md)
- [Examples](examples/basic-router.md)

## License

WRTKit is released under the [MIT License](https://github.com/yourusername/wrtkit/blob/main/LICENSE).
