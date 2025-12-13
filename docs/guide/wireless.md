# Wireless Configuration

Configure WiFi radios and interfaces for access points, mesh networks, and client connections.

## Radio Configuration

Radios are physical wireless hardware. Configure them before creating WiFi interfaces.

### Basic Radio Setup

```python
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)
```

### Radio Options

| Method | Description | Values |
|--------|-------------|--------|
| `channel(n)` | WiFi channel | 1-13 (2.4GHz), 36-165 (5GHz) |
| `htmode(mode)` | Channel width | HT20, HT40, VHT80, VHT160 |
| `country(code)` | Country code | US, GB, DE, etc. |
| `disabled(bool)` | Enable/disable | True/False |
| `txpower(dbm)` | TX power | 1-30 (dBm) |

### Dual-Band Configuration

```python
# 2.4 GHz radio
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .txpower(20)

# 5 GHz radio
config.wireless.radio("radio1") \
    .channel(149) \
    .htmode("VHT80") \
    .country("US") \
    .txpower(23)
```

## WiFi Interfaces

WiFi interfaces are virtual interfaces on radios.

### Access Point (AP)

Create a standard WiFi access point:

```python
config.wireless.wifi_iface("default_ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("MySecurePassword")
```

### Multiple APs

Create multiple APs on the same radio:

```python
# Main AP
config.wireless.wifi_iface("ap_main") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MainNetwork") \
    .encryption("psk2") \
    .key("password1")

# Guest AP
config.wireless.wifi_iface("ap_guest") \
    .device("radio0") \
    .mode("ap") \
    .network("guest") \
    .ssid("GuestNetwork") \
    .encryption("psk2") \
    .key("password2")
```

## Encryption Types

### WPA2-PSK (Recommended)

```python
config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("SecurePassword123")
```

### WPA3-SAE (Most Secure)

```python
config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .ssid("MyNetwork") \
    .encryption("sae") \
    .key("SecurePassword123")
```

### WPA2/WPA3 Mixed Mode

```python
config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .ssid("MyNetwork") \
    .encryption("sae-mixed") \
    .key("SecurePassword123")
```

### Open Network (No Encryption)

```python
config.wireless.wifi_iface("open_ap") \
    .device("radio0") \
    .mode("ap") \
    .ssid("FreeWiFi") \
    .encryption("none")
```

## 802.11r Fast Roaming

Enable fast roaming for seamless handoff between APs:

```python
config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("RoamingNetwork") \
    .encryption("psk2") \
    .key("password") \
    .ieee80211r(True) \
    .ft_over_ds(True) \
    .ft_psk_generate_local(True)
```

Configure the same on all APs with the same SSID for roaming to work.

## Mesh Networking

### Mesh Interface

Create a wireless mesh interface:

```python
config.wireless.wifi_iface("mesh0") \
    .device("radio1") \
    .mode("mesh") \
    .ifname("mesh0") \
    .network("mesh0") \
    .mesh_id("my-mesh-network") \
    .encryption("sae") \
    .key("mesh-password") \
    .mesh_fwding(False) \
    .mcast_rate(18000)
```

### Mesh Options

| Method | Description | Values |
|--------|-------------|--------|
| `mesh_id(id)` | Mesh network ID | Any string |
| `mesh_fwding(bool)` | Mesh forwarding | True/False |
| `mcast_rate(rate)` | Multicast rate | 6000, 12000, 18000, etc. |

## WiFi Interface Options

| Method | Description | Example |
|--------|-------------|---------|
| `device(radio)` | Radio to use | `.device("radio0")` |
| `mode(mode)` | Interface mode | `.mode("ap")` |
| `network(net)` | Network to join | `.network("lan")` |
| `ssid(name)` | Network name | `.ssid("MyWiFi")` |
| `encryption(type)` | Encryption | `.encryption("psk2")` |
| `key(password)` | Password/key | `.key("password")` |
| `ifname(name)` | Interface name | `.ifname("mesh0")` |

## Complete Example

Full dual-band setup with roaming:

```python
from wrtkit import UCIConfig

config = UCIConfig()

# 2.4 GHz Radio
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)

# 5 GHz Radio
config.wireless.radio("radio1") \
    .channel(149) \
    .htmode("VHT80") \
    .country("US") \
    .disabled(False)

# 2.4 GHz AP
config.wireless.wifi_iface("ap_2g") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork-2G") \
    .encryption("psk2") \
    .key("SecurePassword123") \
    .ieee80211r(True) \
    .ft_over_ds(True) \
    .ft_psk_generate_local(True)

# 5 GHz AP
config.wireless.wifi_iface("ap_5g") \
    .device("radio1") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork-5G") \
    .encryption("psk2") \
    .key("SecurePassword123") \
    .ieee80211r(True) \
    .ft_over_ds(True) \
    .ft_psk_generate_local(True)

# 5 GHz Mesh (for interconnecting routers)
config.wireless.wifi_iface("mesh0") \
    .device("radio1") \
    .mode("mesh") \
    .ifname("mesh0") \
    .network("mesh0") \
    .mesh_id("BackhaulMesh") \
    .encryption("sae") \
    .key("MeshPassword123") \
    .mesh_fwding(False) \
    .mcast_rate(18000)
```

## See Also

- [Network Configuration](network.md) - Configure network interfaces
- [Mesh Network Example](../examples/mesh-network.md) - Complete mesh setup
- [API Reference](../api/wireless.md) - Detailed API documentation
