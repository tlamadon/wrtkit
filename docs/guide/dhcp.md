# DHCP Configuration

Configure DHCP servers for automatic IP address assignment to clients.

## Basic DHCP Server

```python
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h") \
    .ignore(False)
```

This creates a DHCP server:

- On the `lan` interface
- Starting at `.100` (e.g., 192.168.1.100)
- With 150 addresses available
- Lease time of 12 hours
- Enabled (not ignored)

## DHCP Options

| Method | Description | Example |
|--------|-------------|---------|
| `interface(name)` | Interface to serve | `.interface("lan")` |
| `start(n)` | Starting offset | `.start(100)` |
| `limit(n)` | Number of addresses | `.limit(150)` |
| `leasetime(time)` | Lease duration | `.leasetime("12h")` |
| `ignore(bool)` | Disable server | `.ignore(True)` |

## Lease Time Format

Lease times can be specified in various formats:

- `"12h"` - 12 hours
- `"24h"` - 24 hours (1 day)
- `"7d"` - 7 days
- `"infinite"` - Never expire

## IP Address Range

The IP range is calculated from the interface's IP address:

```python
# LAN interface: 192.168.1.1/24
config.network.interface("lan") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

# DHCP: 192.168.1.100 - 192.168.1.249
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150)
```

## Multiple DHCP Servers

Configure DHCP for different networks:

```python
# Main LAN
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")

# Guest Network
config.dhcp.dhcp("guest") \
    .interface("guest") \
    .start(50) \
    .limit(100) \
    .leasetime("1h")
```

## Disabling DHCP

Disable DHCP on an interface:

```python
config.dhcp.dhcp("wan") \
    .interface("wan") \
    .ignore(True)
```

Or simply don't configure DHCP for that interface.

## Complete Example

DHCP configuration for a multi-network setup:

```python
from wrtkit import UCIConfig

config = UCIConfig()

# Main LAN: 192.168.1.0/24
config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")

# Guest Network: 192.168.10.0/24
config.network.interface("guest") \
    .device("br-guest") \
    .proto("static") \
    .ipaddr("192.168.10.1") \
    .netmask("255.255.255.0")

config.dhcp.dhcp("guest") \
    .interface("guest") \
    .start(50) \
    .limit(200) \
    .leasetime("1h")

# IoT Network: 192.168.20.0/24
config.network.interface("iot") \
    .device("br-iot") \
    .proto("static") \
    .ipaddr("192.168.20.1") \
    .netmask("255.255.255.0")

config.dhcp.dhcp("iot") \
    .interface("iot") \
    .start(10) \
    .limit(240) \
    .leasetime("24h")
```

## Best Practices

### Lease Times

- **Home LAN**: 12-24 hours (devices are mostly static)
- **Guest Network**: 1-4 hours (high turnover)
- **IoT Devices**: 24 hours - 7 days (mostly static, but may change)

### Address Ranges

Reserve addresses for static assignments:

```python
# Reserve .1-.99 for static IPs, use .100-.249 for DHCP
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150)  # 192.168.1.100 - 192.168.1.249
```

This leaves `192.168.1.1` - `192.168.1.99` for:
- Gateway (`.1`)
- Servers
- Printers
- Access points
- Other static devices

## See Also

- [Network Configuration](network.md) - Configure network interfaces
- [Basic Router Example](../examples/basic-router.md) - Complete router setup
- [API Reference](../api/dhcp.md) - Detailed API documentation
