# Network API

Network configuration classes.

## NetworkConfig

::: wrtkit.network.NetworkConfig
    options:
      show_root_heading: true
      members:
        - add_device
        - add_interface
        - get_commands

## NetworkDevice

::: wrtkit.network.NetworkDevice
    options:
      show_root_heading: true
      members:
        - with_name
        - with_type
        - with_port
        - with_ifname
        - with_vid

## NetworkInterface

::: wrtkit.network.NetworkInterface
    options:
      show_root_heading: true
      members:
        - with_device
        - with_proto
        - with_ipaddr
        - with_netmask
        - with_gateway
        - with_master
        - with_mtu
        - with_routing_algo
        - with_gw_mode
        - with_gw_bandwidth
        - with_hop_penalty
        - with_orig_interval
        - with_static_ip
        - with_dhcp

## Usage Example

```python
from wrtkit import UCIConfig
from wrtkit.network import NetworkDevice, NetworkInterface

config = UCIConfig()

# Create a bridge
device = NetworkDevice("br_lan")\
    .with_name("br-lan")\
    .with_type("bridge")\
    .with_port("lan1")\
    .with_port("lan2")
config.network.add_device(device)

# Create an interface
interface = NetworkInterface("lan")\
    .with_device("br-lan")\
    .with_static_ip("192.168.1.1", "255.255.255.0")
config.network.add_interface(interface)
```

## See Also

- [Network Guide](../guide/network.md)
- [API Overview](config.md)
