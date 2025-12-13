# Basic Router Example

A simple home router configuration with LAN, WAN, WiFi, DHCP, and firewall.

## Complete Code

```python
from wrtkit import UCIConfig, SSHConnection

# Create configuration
config = UCIConfig()

# LAN Interface
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

# WAN Interface
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")

# WiFi Radio
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)

# WiFi Access Point
config.wireless.wifi_iface("default_ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("MySecurePassword123")

# DHCP Server
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")

# Firewall - LAN Zone
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

# Firewall - WAN Zone
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .mtu_fix(True) \
    .add_network("wan")

# Firewall - Allow LAN → WAN
config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")

# Export to file
config.save_to_file("basic_router.sh")

# Or apply via SSH
# with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
#     config.apply(ssh)
```

## What This Does

- **LAN**: Static IP `192.168.1.1/24` on `eth0`
- **WAN**: DHCP client on `eth1`
- **WiFi**: 2.4GHz AP on channel 11 with WPA2
- **DHCP**: Serves `192.168.1.100` - `192.168.1.249`
- **Firewall**: Allows LAN→WAN, blocks WAN→LAN

## Customization

### Change LAN IP

```python
config.network.interface("lan") \
    .ipaddr("192.168.10.1")  # Change to your preference
```

### Change WiFi Settings

```python
config.wireless.radio("radio0") \
    .channel(6)  # Different channel

config.wireless.wifi_iface("default_ap") \
    .ssid("YourNetworkName") \
    .key("YourSecurePassword")
```

### Adjust DHCP Range

```python
config.dhcp.dhcp("lan") \
    .start(50) \
    .limit(200)  # 192.168.1.50 - 192.168.1.249
```

## See Also

- [Mesh Network Example](mesh-network.md)
- [Network Guide](../guide/network.md)
- [Wireless Guide](../guide/wireless.md)
