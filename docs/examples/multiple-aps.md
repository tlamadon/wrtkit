# Multiple Access Points

Configure multiple WiFi networks on the same router.

## Dual-Band with Guest Network

```python
from wrtkit import UCIConfig

config = UCIConfig()

# Main 2.4 GHz AP
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US")

config.wireless.wifi_iface("ap_main_2g") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("Home-WiFi") \
    .encryption("psk2") \
    .key("MainPassword123")

# Main 5 GHz AP
config.wireless.radio("radio1") \
    .channel(149) \
    .htmode("VHT80") \
    .country("US")

config.wireless.wifi_iface("ap_main_5g") \
    .device("radio1") \
    .mode("ap") \
    .network("lan") \
    .ssid("Home-WiFi-5G") \
    .encryption("psk2") \
    .key("MainPassword123")

# Guest 2.4 GHz AP (on same radio as main)
config.wireless.wifi_iface("ap_guest") \
    .device("radio0") \
    .mode("ap") \
    .network("guest") \
    .ssid("Guest-WiFi") \
    .encryption("psk2") \
    .key("GuestPassword123")

# Guest network configuration
config.network.interface("guest") \
    .device("br-guest") \
    .proto("static") \
    .ipaddr("192.168.10.1") \
    .netmask("255.255.255.0")

config.dhcp.dhcp("guest") \
    .interface("guest") \
    .start(50) \
    .limit(200) \
    .leasetime("1h")

# Guest firewall (isolated)
config.firewall.zone(2) \
    .name("guest") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("guest")

config.firewall.forwarding(1) \
    .src("guest") \
    .dest("wan")
```

## What This Creates

- **Home WiFi (2.4GHz)**: For older devices
- **Home WiFi (5GHz)**: For faster devices
- **Guest WiFi**: Isolated, internet-only access

## IoT Network

Add a separate network for IoT devices:

```python
# IoT AP (2.4 GHz only, IoT devices often don't support 5GHz)
config.wireless.wifi_iface("ap_iot") \
    .device("radio0") \
    .mode("ap") \
    .network("iot") \
    .ssid("IoT-Devices") \
    .encryption("psk2") \
    .key("IoTPassword123")

# IoT network
config.network.interface("iot") \
    .device("br-iot") \
    .proto("static") \
    .ipaddr("192.168.20.1") \
    .netmask("255.255.255.0")

config.dhcp.dhcp("iot") \
    .interface("iot") \
    .start(10) \
    .limit(240) \
    .leasetime("24h")

# IoT firewall (isolated, internet only)
config.firewall.zone(3) \
    .name("iot") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .add_network("iot")

config.firewall.forwarding(2) \
    .src("iot") \
    .dest("wan")
```

## See Also

- [Wireless Guide](../guide/wireless.md)
- [Firewall Guide](../guide/firewall.md)
- [Advanced Firewall Example](advanced-firewall.md)
