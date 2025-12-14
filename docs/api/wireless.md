# Wireless API

Wireless configuration classes.

## WirelessConfig

::: wrtkit.wireless.WirelessConfig
    options:
      show_root_heading: true
      members:
        - add_radio
        - add_interface
        - get_commands

## WirelessRadio

::: wrtkit.wireless.WirelessRadio
    options:
      show_root_heading: true
      members:
        - with_channel
        - with_htmode
        - with_country
        - with_disabled
        - with_txpower

## WirelessInterface

::: wrtkit.wireless.WirelessInterface
    options:
      show_root_heading: true
      members:
        - with_device
        - with_mode
        - with_network
        - with_ssid
        - with_encryption
        - with_key
        - with_ifname
        - with_mesh_id
        - with_mesh_fwding
        - with_mcast_rate
        - with_ieee80211r
        - with_ft_over_ds
        - with_ft_psk_generate_local
        - with_ap
        - with_mesh

## Usage Example

```python
from wrtkit import UCIConfig
from wrtkit.wireless import WirelessRadio, WirelessInterface

config = UCIConfig()

# Create a radio
radio = WirelessRadio("radio0")\
    .with_channel(11)\
    .with_htmode("HT20")\
    .with_country("US")\
    .with_disabled(False)
config.wireless.add_radio(radio)

# Create an AP interface
ap = WirelessInterface("ap")\
    .with_device("radio0")\
    .with_ap("MyNetwork", "psk2", "password123")\
    .with_network("lan")
config.wireless.add_interface(ap)
```

## See Also

- [Wireless Guide](../guide/wireless.md)
- [API Overview](config.md)
