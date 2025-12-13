# Network Configuration

Network configuration in WRTKit covers devices (bridges, VLANs) and interfaces (LAN, WAN, etc.).

## Network Interfaces

Network interfaces define logical network connections.

### Static IP Interface

```python
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0") \
    .gateway("192.168.1.254")
```

### DHCP Client Interface

```python
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")
```

### Interface Options

| Method | Description | Example |
|--------|-------------|---------|
| `device(name)` | Physical device or bridge | `.device("eth0")` |
| `proto(protocol)` | Protocol type | `.proto("static")` |
| `ipaddr(ip)` | IP address | `.ipaddr("192.168.1.1")` |
| `netmask(mask)` | Network mask | `.netmask("255.255.255.0")` |
| `gateway(ip)` | Default gateway | `.gateway("192.168.1.254")` |
| `mtu(size)` | MTU size | `.mtu(1500)` |

### Supported Protocols

- `static` - Static IP address
- `dhcp` - DHCP client
- `batadv` - BATMAN-ADV mesh protocol
- `batadv_hardif` - BATMAN-ADV hard interface

## Network Devices

Network devices represent physical or virtual network hardware.

### Bridge Device

Create a bridge combining multiple ports:

```python
config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("lan2") \
    .add_port("lan3") \
    .add_port("lan4")

# Use the bridge in an interface
config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")
```

### VLAN Device (802.1Q)

Create a VLAN on top of a physical interface:

```python
config.network.device("vlan10") \
    .type("8021q") \
    .ifname("eth0") \
    .vid(10) \
    .name("eth0.10")

# Use the VLAN in an interface
config.network.interface("guest") \
    .device("eth0.10") \
    .proto("static") \
    .ipaddr("192.168.10.1") \
    .netmask("255.255.255.0")
```

### Device Options

| Method | Description | Example |
|--------|-------------|---------|
| `name(name)` | Device name | `.name("br-lan")` |
| `type(type)` | Device type | `.type("bridge")` |
| `add_port(port)` | Add bridge port | `.add_port("lan1")` |
| `ifname(name)` | Parent interface | `.ifname("eth0")` |
| `vid(id)` | VLAN ID | `.vid(10)` |

## BATMAN-ADV Mesh Networking

BATMAN-ADV is a mesh networking protocol for OpenWRT.

### BATMAN-ADV Interface

```python
config.network.interface("bat0") \
    .proto("batadv") \
    .routing_algo("BATMAN_IV") \
    .gw_mode("server") \
    .gw_bandwidth("10000/10000") \
    .hop_penalty(30) \
    .orig_interval(1000)
```

### BATMAN-ADV Options

| Method | Description | Example |
|--------|-------------|---------|
| `routing_algo(algo)` | Routing algorithm | `.routing_algo("BATMAN_IV")` |
| `gw_mode(mode)` | Gateway mode | `.gw_mode("server")` |
| `gw_bandwidth(bw)` | Gateway bandwidth | `.gw_bandwidth("10000/10000")` |
| `hop_penalty(penalty)` | Hop penalty | `.hop_penalty(30)` |
| `orig_interval(ms)` | Originator interval | `.orig_interval(1000)` |

### BATMAN-ADV Hard Interface

Link a physical interface to the mesh:

```python
config.network.interface("mesh0") \
    .proto("batadv_hardif") \
    .master("bat0") \
    .mtu(1532)
```

### BATMAN-ADV VLAN

Create a VLAN on the mesh interface:

```python
config.network.device("bat0_vlan10") \
    .type("8021q") \
    .ifname("bat0") \
    .vid(10) \
    .name("bat0.10")

# Add to LAN bridge
config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("bat0.10")
```

## Complete Example

A complete network configuration with LAN, WAN, and mesh:

```python
from wrtkit import UCIConfig

config = UCIConfig()

# LAN Bridge
config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("lan2")

config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

# WAN
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")

# BATMAN-ADV Mesh
config.network.interface("bat0") \
    .proto("batadv") \
    .routing_algo("BATMAN_IV") \
    .gw_mode("server")

config.network.interface("mesh0") \
    .proto("batadv_hardif") \
    .master("bat0")

# BATMAN VLAN
config.network.device("bat0_vlan10") \
    .type("8021q") \
    .ifname("bat0") \
    .vid(10) \
    .name("bat0.10")

# Add mesh VLAN to bridge
config.network.device("br_lan") \
    .add_port("bat0.10")
```

## See Also

- [Wireless Configuration](wireless.md) - Configure WiFi for mesh
- [API Reference](../api/network.md) - Detailed API documentation
- [Mesh Network Example](../examples/mesh-network.md) - Complete mesh setup
