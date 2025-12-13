# Wireless API

Wireless configuration classes and builders.

## WirelessConfig

::: wrtkit.wireless.WirelessConfig
    options:
      show_root_heading: true
      members:
        - radio
        - wifi_iface
        - get_commands

## RadioBuilder

::: wrtkit.wireless.RadioBuilder
    options:
      show_root_heading: true
      members:
        - channel
        - htmode
        - country
        - disabled
        - txpower

## WiFiInterfaceBuilder

::: wrtkit.wireless.WiFiInterfaceBuilder
    options:
      show_root_heading: true
      members:
        - device
        - mode
        - network
        - ssid
        - encryption
        - key
        - ifname
        - mesh_id
        - mesh_fwding
        - mcast_rate
        - ieee80211r
        - ft_over_ds
        - ft_psk_generate_local

## Usage Example

```python
config = UCIConfig()

# Configure radio
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US")

# Create access point
config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("password")
```

## See Also

- [Wireless Guide](../guide/wireless.md)
- [API Overview](config.md)
