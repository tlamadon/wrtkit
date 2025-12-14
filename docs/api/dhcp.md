# DHCP API

DHCP configuration classes.

## DHCPConfig

::: wrtkit.dhcp.DHCPConfig
    options:
      show_root_heading: true
      members:
        - add_dhcp
        - get_commands

## DHCPSection

::: wrtkit.dhcp.DHCPSection
    options:
      show_root_heading: true
      members:
        - with_interface
        - with_start
        - with_limit
        - with_leasetime
        - with_ignore
        - with_range

## Usage Example

```python
from wrtkit import UCIConfig
from wrtkit.dhcp import DHCPSection

config = UCIConfig()

# Create DHCP section
section = DHCPSection("lan")\
    .with_interface("lan")\
    .with_start(100)\
    .with_limit(150)\
    .with_leasetime("12h")

config.dhcp.add_dhcp(section)
```

## See Also

- [DHCP Guide](../guide/dhcp.md)
- [API Overview](config.md)
