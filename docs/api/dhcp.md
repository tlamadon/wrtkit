# DHCP API

DHCP configuration classes and builders.

## DHCPConfig

::: wrtkit.dhcp.DHCPConfig
    options:
      show_root_heading: true
      members:
        - dhcp
        - get_commands

## DHCPBuilder

::: wrtkit.dhcp.DHCPBuilder
    options:
      show_root_heading: true
      members:
        - interface
        - start
        - limit
        - leasetime
        - ignore

## Usage Example

```python
config = UCIConfig()

config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")
```

## See Also

- [DHCP Guide](../guide/dhcp.md)
- [API Overview](config.md)
