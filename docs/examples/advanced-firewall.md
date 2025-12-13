# Advanced Firewall Example

Complex firewall configuration with multiple isolated networks.

## Multi-Zone Setup

```python
from wrtkit import UCIConfig

config = UCIConfig()

# Zone 0: LAN (Trusted)
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

# Zone 1: WAN (Untrusted)
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .mtu_fix(True) \
    .add_network("wan")

# Zone 2: Guest (Isolated, internet only)
config.firewall.zone(2) \
    .name("guest") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("guest")

# Zone 3: IoT (Isolated, internet only)
config.firewall.zone(3) \
    .name("iot") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("iot")

# Zone 4: DMZ (Servers)
config.firewall.zone(4) \
    .name("dmz") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("dmz")

# Forwarding Rules
config.firewall.forwarding(0).src("lan").dest("wan")      # LAN → Internet
config.firewall.forwarding(1).src("lan").dest("guest")    # LAN → Guest (admin)
config.firewall.forwarding(2).src("lan").dest("iot")      # LAN → IoT (admin)
config.firewall.forwarding(3).src("lan").dest("dmz")      # LAN → DMZ (admin)
config.firewall.forwarding(4).src("guest").dest("wan")    # Guest → Internet only
config.firewall.forwarding(5).src("iot").dest("wan")      # IoT → Internet only
config.firewall.forwarding(6).src("dmz").dest("wan")      # DMZ → Internet
```

## Traffic Matrix

| From/To | LAN | WAN | Guest | IoT | DMZ |
|---------|-----|-----|-------|-----|-----|
| **LAN** | ✓   | ✓   | ✓     | ✓   | ✓   |
| **WAN** | ✗   | -   | ✗     | ✗   | ✗   |
| **Guest**| ✗  | ✓   | ✗     | ✗   | ✗   |
| **IoT** | ✗   | ✓   | ✗     | ✗   | ✗   |
| **DMZ** | ✗   | ✓   | ✗     | ✗   | ✗   |

✓ = Allowed, ✗ = Blocked

## Network Definitions

```python
# LAN: 192.168.1.0/24
config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

# Guest: 192.168.10.0/24
config.network.interface("guest") \
    .device("br-guest") \
    .proto("static") \
    .ipaddr("192.168.10.1") \
    .netmask("255.255.255.0")

# IoT: 192.168.20.0/24
config.network.interface("iot") \
    .device("br-iot") \
    .proto("static") \
    .ipaddr("192.168.20.1") \
    .netmask("255.255.255.0")

# DMZ: 192.168.30.0/24
config.network.interface("dmz") \
    .device("br-dmz") \
    .proto("static") \
    .ipaddr("192.168.30.1") \
    .netmask("255.255.255.0")
```

## See Also

- [Firewall Guide](../guide/firewall.md)
- [Network Guide](../guide/network.md)
- [Multiple APs Example](multiple-aps.md)
