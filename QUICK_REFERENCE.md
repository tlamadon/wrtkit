# WRTKit Quick Reference

## Installation
```bash
pip install wrtkit
```

## Basic Usage

### Import
```python
from wrtkit import UCIConfig, SSHConnection
```

### Create Config
```python
config = UCIConfig()
```

## Network Configuration

### Static Interface
```python
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0") \
    .gateway("192.168.1.254")
```

### DHCP Client Interface
```python
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")
```

### Bridge Device
```python
config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("lan2") \
    .add_port("lan3")
```

### VLAN Device
```python
config.network.device("vlan10") \
    .type("8021q") \
    .ifname("eth0") \
    .vid(10) \
    .name("eth0.10")
```

### BATMAN-ADV Interface
```python
config.network.interface("bat0") \
    .proto("batadv") \
    .routing_algo("BATMAN_IV") \
    .gw_mode("server") \
    .gw_bandwidth("10000/10000") \
    .hop_penalty(30) \
    .orig_interval(1000)
```

### BATMAN-ADV Hardif
```python
config.network.interface("mesh0") \
    .proto("batadv_hardif") \
    .master("bat0") \
    .mtu(1532)
```

## Wireless Configuration

### Radio
```python
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False) \
    .txpower(20)
```

### Access Point
```python
config.wireless.wifi_iface("default_ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("MyPassword")
```

### Access Point with 802.11r Fast Roaming
```python
config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("MyPassword") \
    .ieee80211r(True) \
    .ft_over_ds(True) \
    .ft_psk_generate_local(True)
```

### Mesh Interface
```python
config.wireless.wifi_iface("mesh0") \
    .device("radio1") \
    .mode("mesh") \
    .ifname("mesh0") \
    .network("mesh0") \
    .mesh_id("my-mesh") \
    .encryption("sae") \
    .key("mesh-password") \
    .mesh_fwding(False) \
    .mcast_rate(18000)
```

## DHCP Configuration

### DHCP Server
```python
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h") \
    .ignore(False)
```

### Disable DHCP
```python
config.dhcp.dhcp("guest") \
    .interface("guest") \
    .ignore(True)
```

## Firewall Configuration

### LAN Zone (Permissive)
```python
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")
```

### WAN Zone (Restrictive with NAT)
```python
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .mtu_fix(True) \
    .add_network("wan")
```

### Zone with Multiple Networks
```python
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan") \
    .add_network("guest")
```

### Forwarding Rule
```python
config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")
```

## Output Methods

### Generate Script
```python
script = config.to_script(include_commit=True, include_reload=True)
print(script)
```

### Save to File
```python
config.save_to_file("config.sh", include_commit=True, include_reload=True)
```

### Get Commands List
```python
commands = config.get_all_commands()
for cmd in commands:
    print(cmd.to_string())
```

## SSH Operations

### Connect with Password
```python
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    password="your-password"
)
```

### Connect with SSH Key
```python
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    key_filename="/path/to/id_rsa"
)
```

### Connect with Custom Port
```python
ssh = SSHConnection(
    host="192.168.1.1",
    port=2222,
    username="root",
    password="your-password",
    timeout=60
)
```

### Context Manager
```python
with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
    diff = config.diff(ssh)
    print(diff)
```

### Compare Configuration
```python
diff = config.diff(ssh)
print(diff)

if diff.is_empty():
    print("No changes needed")
else:
    print("Changes detected:")
    print(diff)
```

### Apply Configuration
```python
# With auto-commit and auto-reload
config.apply(ssh, auto_commit=True, auto_reload=True)

# Dry run (show what would be executed)
config.apply(ssh, dry_run=True)

# Manual control
config.apply(ssh, auto_commit=False, auto_reload=False)
ssh.commit_changes()
ssh.reload_config()
```

### Execute Custom Commands
```python
stdout, stderr, exit_code = ssh.execute("uci show network")
print(stdout)

# Get current UCI config
network_config = ssh.get_uci_config("network")
print(network_config)
```

## Common Patterns

### Complete Router Setup
```python
config = UCIConfig()

# LAN
config.network.device("br_lan").name("br-lan").type("bridge") \
    .add_port("lan1").add_port("lan2")
config.network.interface("lan").device("br-lan").proto("static") \
    .ipaddr("192.168.1.1").netmask("255.255.255.0")

# WAN
config.network.interface("wan").device("eth1").proto("dhcp")

# Wireless AP
config.wireless.radio("radio0").channel(11).htmode("HT20").country("US")
config.wireless.wifi_iface("ap").device("radio0").mode("ap") \
    .network("lan").ssid("MyNetwork").encryption("psk2").key("Password")

# DHCP
config.dhcp.dhcp("lan").interface("lan").start(100).limit(150).leasetime("12h")

# Firewall
config.firewall.zone(0).name("lan").input("ACCEPT").output("ACCEPT") \
    .forward("ACCEPT").add_network("lan")
config.firewall.zone(1).name("wan").input("REJECT").output("ACCEPT") \
    .forward("REJECT").masq(True).add_network("wan")
config.firewall.forwarding(0).src("lan").dest("wan")

# Apply
with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
    config.apply(ssh)
```

## Encryption Types

- `"none"` - No encryption
- `"psk"` - WPA-PSK
- `"psk2"` - WPA2-PSK
- `"psk-mixed"` - WPA/WPA2 mixed
- `"sae"` - WPA3-SAE
- `"sae-mixed"` - WPA2/WPA3 mixed

## HT Modes

- `"HT20"` - 20 MHz channel width
- `"HT40"` - 40 MHz channel width
- `"VHT20"` - 20 MHz (802.11ac)
- `"VHT40"` - 40 MHz (802.11ac)
- `"VHT80"` - 80 MHz (802.11ac)
- `"VHT160"` - 160 MHz (802.11ac)

## Firewall Policies

- `"ACCEPT"` - Allow traffic
- `"REJECT"` - Reject with ICMP error
- `"DROP"` - Silently drop traffic

## Boolean Values

Use Python booleans: `True` or `False`
- Automatically converted to UCI format (`'1'` or `'0'`)
