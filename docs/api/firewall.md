# Firewall API

Firewall configuration classes.

## FirewallConfig

::: wrtkit.firewall.FirewallConfig
    options:
      show_root_heading: true
      members:
        - add_zone
        - add_forwarding
        - get_commands

## FirewallZone

::: wrtkit.firewall.FirewallZone
    options:
      show_root_heading: true
      members:
        - with_name
        - with_input
        - with_output
        - with_forward
        - with_masq
        - with_mtu_fix
        - with_network
        - with_networks
        - with_default_policies

## FirewallForwarding

::: wrtkit.firewall.FirewallForwarding
    options:
      show_root_heading: true
      members:
        - with_src
        - with_dest

## Usage Example

```python
from wrtkit import UCIConfig
from wrtkit.firewall import FirewallZone, FirewallForwarding

config = UCIConfig()

# Create a LAN zone
lan_zone = FirewallZone(0)\
    .with_name("lan")\
    .with_input("ACCEPT")\
    .with_output("ACCEPT")\
    .with_forward("ACCEPT")\
    .with_network("lan")
config.firewall.add_zone(lan_zone)

# Create a WAN zone
wan_zone = FirewallZone(1)\
    .with_name("wan")\
    .with_input("REJECT")\
    .with_masq(True)\
    .with_mtu_fix(True)\
    .with_network("wan")
config.firewall.add_zone(wan_zone)

# Create a forwarding rule
forwarding = FirewallForwarding(0)\
    .with_src("lan")\
    .with_dest("wan")
config.firewall.add_forwarding(forwarding)
```

## See Also

- [Firewall Guide](../guide/firewall.md)
- [API Overview](config.md)
