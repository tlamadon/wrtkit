# Mesh Network Example

Advanced configuration with BATMAN-ADV mesh networking based on the `router.cfg` example.

## Complete Code

```python
from wrtkit import UCIConfig

config = UCIConfig()

# LAN Bridge
config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("lan2") \
    .add_port("lan3")

config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.10.1") \
    .netmask("255.255.255.0")

# WAN
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")

# BATMAN-ADV
config.network.interface("bat0") \
    .proto("batadv") \
    .routing_algo("BATMAN_IV") \
    .gw_mode("server") \
    .gw_bandwidth("10000/10000") \
    .hop_penalty(30) \
    .orig_interval(1000)

# BATMAN VLAN
config.network.device("bat0_vlan10") \
    .type("8021q") \
    .ifname("bat0") \
    .vid(10) \
    .name("bat0.10")

# Add to bridge
config.network.device("br_lan") \
    .add_port("bat0.10")

# Mesh hardif
config.network.interface("mesh0") \
    .proto("batadv_hardif") \
    .master("bat0")

# 2.4 GHz Radio
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)

# 5 GHz Radio
config.wireless.radio("radio1") \
    .channel(149) \
    .country("US") \
    .disabled(False)

# 2.4 GHz AP
config.wireless.wifi_iface("ap_two") \
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
config.wireless.wifi_iface("ap_five") \
    .device("radio1") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork-5G") \
    .encryption("psk2") \
    .key("SecurePassword123") \
    .ieee80211r(True) \
    .ft_over_ds(True) \
    .ft_psk_generate_local(True)

# Mesh Interface
config.wireless.wifi_iface("mesh0_iface") \
    .device("radio1") \
    .mode("mesh") \
    .ifname("mesh0") \
    .network("mesh0") \
    .mesh_id("MeshBackhaul") \
    .encryption("sae") \
    .key("MeshSecurePassword") \
    .mesh_fwding(False) \
    .mcast_rate(18000)

# DHCP
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h") \
    .ignore(False)

# Firewall
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .mtu_fix(True) \
    .add_network("wan")

config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")

# Save configuration
config.save_to_file("mesh_router.sh")
```

## What This Does

- **LAN Bridge**: Combines lan1, lan2, lan3, and mesh VLAN
- **Mesh Network**: BATMAN-ADV with 5GHz wireless backhaul
- **Dual-Band WiFi**: 2.4GHz and 5GHz APs with 802.11r roaming
- **Gateway**: Acts as mesh gateway with internet sharing

## Multi-Router Setup

Deploy this configuration to multiple routers. They will:

1. Form a mesh network via 5GHz
2. Share a common LAN bridge via the mesh
3. Provide 802.11r fast roaming
4. One router acts as gateway to internet

### Router 1 (Gateway)

```python
config.network.interface("bat0") \
    .gw_mode("server")  # Gateway mode

config.network.interface("wan") \
    .proto("dhcp")  # Has WAN connection
```

### Router 2, 3, etc (Mesh Nodes)

```python
config.network.interface("bat0") \
    .gw_mode("client")  # Client mode

# No WAN interface needed
```

## See Also

- [Network Guide](../guide/network.md) - BATMAN-ADV details
- [Wireless Guide](../guide/wireless.md) - Mesh configuration
- [Basic Router](basic-router.md) - Simpler example
