# Network API

Network configuration classes and builders.

## NetworkConfig

::: wrtkit.network.NetworkConfig
    options:
      show_root_heading: true
      members:
        - device
        - interface
        - get_commands

## DeviceBuilder

::: wrtkit.network.DeviceBuilder
    options:
      show_root_heading: true
      members:
        - name
        - type
        - add_port
        - ifname
        - vid

## InterfaceBuilder

::: wrtkit.network.InterfaceBuilder
    options:
      show_root_heading: true
      members:
        - device
        - proto
        - ipaddr
        - netmask
        - gateway
        - master
        - mtu
        - routing_algo
        - gw_mode
        - gw_bandwidth
        - hop_penalty
        - orig_interval

## Usage Example

```python
config = UCIConfig()

# Create a bridge
config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("lan2")

# Create an interface
config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")
```

## See Also

- [Network Guide](../guide/network.md)
- [API Overview](config.md)
