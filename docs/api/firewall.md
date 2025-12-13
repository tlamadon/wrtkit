# Firewall API

Firewall configuration classes and builders.

## FirewallConfig

::: wrtkit.firewall.FirewallConfig
    options:
      show_root_heading: true
      members:
        - zone
        - forwarding
        - get_commands

## ZoneBuilder

::: wrtkit.firewall.ZoneBuilder
    options:
      show_root_heading: true
      members:
        - name
        - input
        - output
        - forward
        - masq
        - mtu_fix
        - add_network

## ForwardingBuilder

::: wrtkit.firewall.ForwardingBuilder
    options:
      show_root_heading: true
      members:
        - src
        - dest

## Usage Example

```python
config = UCIConfig()

# Create zone
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

# Create forwarding rule
config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")
```

## See Also

- [Firewall Guide](../guide/firewall.md)
- [API Overview](config.md)
