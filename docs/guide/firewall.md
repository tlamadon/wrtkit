# Firewall Configuration

Configure firewall zones and rules to control traffic flow between networks.

## Firewall Zones

Zones group networks and define default policies for traffic.

### LAN Zone (Permissive)

```python
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")
```

### WAN Zone (Restrictive)

```python
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .mtu_fix(True) \
    .add_network("wan")
```

## Zone Options

| Method | Description | Values |
|--------|-------------|--------|
| `name(name)` | Zone name | Any string |
| `input(policy)` | Incoming traffic | ACCEPT, REJECT, DROP |
| `output(policy)` | Outgoing traffic | ACCEPT, REJECT, DROP |
| `forward(policy)` | Forwarded traffic | ACCEPT, REJECT, DROP |
| `masq(bool)` | Enable NAT | True/False |
| `mtu_fix(bool)` | MSS clamping | True/False |
| `add_network(net)` | Add network | Network name |

## Traffic Policies

- **ACCEPT** - Allow traffic
- **REJECT** - Block with ICMP error message
- **DROP** - Silently discard traffic

## Zone Indexes

Zones are referenced by index (0, 1, 2, etc.). Common convention:

- Zone 0: LAN
- Zone 1: WAN
- Zone 2: Guest
- Zone 3+: Other networks

## Forwarding Rules

Control traffic flow between zones:

```python
config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")
```

This allows traffic from LAN to WAN (internet access).

## Multi-Network Zones

Add multiple networks to a zone:

```python
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan") \
    .add_network("iot") \
    .add_network("servers")
```

## Common Configurations

### Basic Home Router

```python
# LAN - Trust all traffic
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

# WAN - Block incoming, allow outgoing
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .mtu_fix(True) \
    .add_network("wan")

# Allow LAN → WAN
config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")
```

### Guest Network

```python
# Guest zone - Isolated
config.firewall.zone(2) \
    .name("guest") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("guest")

# Allow Guest → WAN only
config.firewall.forwarding(1) \
    .src("guest") \
    .dest("wan")

# Block Guest → LAN (no forwarding rule)
```

### IoT Network (Restricted)

```python
# IoT zone - No forwarding
config.firewall.zone(3) \
    .name("iot") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("iot")

# IoT → WAN only
config.firewall.forwarding(2) \
    .src("iot") \
    .dest("wan")

# Block IoT → LAN (no forwarding rule)
```

## NAT and Masquerading

### Enable NAT

```python
config.firewall.zone(1) \
    .name("wan") \
    .masq(True)  # Enable NAT
```

NAT (masquerading) is required for internet access when using private IP addresses.

### MTU Fix

```python
config.firewall.zone(1) \
    .name("wan") \
    .mtu_fix(True)  # Enable MSS clamping
```

MTU fix (MSS clamping) helps prevent MTU issues with certain ISPs.

## Complete Example

Multi-network firewall setup:

```python
from wrtkit import UCIConfig

config = UCIConfig()

# LAN Zone - Full trust
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

# WAN Zone - Untrusted
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .mtu_fix(True) \
    .add_network("wan")

# Guest Zone - Isolated
config.firewall.zone(2) \
    .name("guest") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("guest")

# IoT Zone - Restricted
config.firewall.zone(3) \
    .name("iot") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("iot")

# Forwarding Rules
config.firewall.forwarding(0).src("lan").dest("wan")
config.firewall.forwarding(1).src("guest").dest("wan")
config.firewall.forwarding(2).src("iot").dest("wan")

# Optional: Allow LAN → Guest for management
# config.firewall.forwarding(3).src("lan").dest("guest")
```

## Traffic Flow Matrix

This configuration results in:

| From ↓ / To → | LAN | WAN | Guest | IoT |
|---------------|-----|-----|-------|-----|
| **LAN**       | ✓   | ✓   | ✗     | ✗   |
| **WAN**       | ✗   | -   | ✗     | ✗   |
| **Guest**     | ✗   | ✓   | ✗     | ✗   |
| **IoT**       | ✗   | ✓   | ✗     | ✗   |

- ✓ = Allowed
- ✗ = Blocked
- \- = N/A

## Best Practices

1. **Default Deny**: Start with restrictive policies, open only what's needed
2. **Zone Isolation**: Keep untrusted networks (Guest, IoT) isolated from LAN
3. **WAN Protection**: Always use `REJECT` or `DROP` for WAN input
4. **Enable NAT**: Use `masq(True)` on WAN for private networks
5. **MTU Fix**: Enable `mtu_fix(True)` if you experience connectivity issues

## See Also

- [Network Configuration](network.md) - Configure network interfaces
- [Advanced Firewall Example](../examples/advanced-firewall.md) - Complex firewall setup
- [API Reference](../api/firewall.md) - Detailed API documentation
