# Your First Configuration

Let's build a complete router configuration step by step, understanding each component.

## The Goal

We'll configure a basic home router with:

- LAN network on `192.168.1.1/24`
- WAN connection via DHCP
- WiFi access point
- DHCP server for LAN clients
- Basic firewall rules

## Step 1: Import and Initialize

```python
from wrtkit import UCIConfig

# Create a new configuration
config = UCIConfig()
```

The `UCIConfig` object is your main entry point. It contains four configuration managers:

- `config.network` - Network devices and interfaces
- `config.wireless` - WiFi radios and interfaces
- `config.dhcp` - DHCP servers
- `config.firewall` - Firewall zones and rules

## Step 2: Configure LAN Network

```python
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")
```

This configures:

- An interface named `lan`
- Using physical device `eth0`
- With a static IP address
- IP: `192.168.1.1`
- Netmask: `255.255.255.0` (24-bit subnet)

The backslash `\` allows us to break the chain across multiple lines for readability.

## Step 3: Configure WAN Connection

```python
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")
```

This configures:

- An interface named `wan`
- Using physical device `eth1`
- To obtain an IP address via DHCP from your ISP

## Step 4: Configure WiFi Radio

```python
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)
```

This configures the wireless radio:

- Radio identifier: `radio0`
- Channel: `11` (2.4 GHz)
- Channel width: `HT20` (20 MHz)
- Country code: `US` (for regulatory compliance)
- Enabled (not disabled)

## Step 5: Create WiFi Access Point

```python
config.wireless.wifi_iface("default_ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyHomeNetwork") \
    .encryption("psk2") \
    .key("MySecurePassword123")
```

This creates a WiFi access point:

- Interface name: `default_ap`
- Using radio: `radio0`
- Mode: `ap` (access point)
- Connected to: `lan` network
- SSID: `MyHomeNetwork` (your WiFi name)
- Encryption: `psk2` (WPA2-PSK)
- Password: `MySecurePassword123`

!!! warning "Security"
    Always use a strong password with at least 12 characters including letters, numbers, and symbols.

## Step 6: Configure DHCP Server

```python
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")
```

This configures a DHCP server:

- For the `lan` interface
- Starting IP: `192.168.1.100`
- Number of addresses: `150` (up to `192.168.1.249`)
- Lease time: `12h` (12 hours)

## Step 7: Configure Firewall Zones

```python
# LAN zone - allow everything
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")
```

LAN zone configuration:

- Zone index: `0`
- Zone name: `lan`
- Input policy: `ACCEPT` (allow incoming traffic)
- Output policy: `ACCEPT` (allow outgoing traffic)
- Forward policy: `ACCEPT` (allow forwarding)
- Networks in this zone: `lan`

```python
# WAN zone - restrict incoming, allow outgoing
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .add_network("wan")
```

WAN zone configuration:

- Zone index: `1`
- Zone name: `wan`
- Input policy: `REJECT` (block incoming traffic)
- Output policy: `ACCEPT` (allow outgoing traffic)
- Forward policy: `REJECT` (don't forward to WAN by default)
- Masquerading: `True` (enable NAT)
- Networks in this zone: `wan`

## Step 8: Configure Forwarding Rule

```python
config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")
```

This allows traffic from LAN to WAN:

- Rule index: `0`
- Source zone: `lan`
- Destination zone: `wan`

This enables internet access for LAN clients.

## Complete Code

Here's the complete configuration:

```python
from wrtkit import UCIConfig

# Initialize
config = UCIConfig()

# Network
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")

# Wireless
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)

config.wireless.wifi_iface("default_ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyHomeNetwork") \
    .encryption("psk2") \
    .key("MySecurePassword123")

# DHCP
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")

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
    .add_network("wan")

config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")

# Save to file
config.save_to_file("my_router.sh")
print("Configuration saved to my_router.sh")
```

## Understanding the Output

Run `config.to_script()` to see the generated UCI commands:

```bash
#!/bin/sh

uci set network.lan='interface'
uci set network.lan.device='eth0'
uci set network.lan.proto='static'
uci set network.lan.ipaddr='192.168.1.1'
uci set network.lan.netmask='255.255.255.0'
# ... more commands ...

uci commit
/etc/init.d/network restart
wifi reload
```

Each method call becomes one or more `uci set` commands. The script:

1. Sets all UCI values
2. Commits the changes
3. Restarts network services
4. Reloads wireless configuration

## Next Steps

- Learn about [Network Configuration](../guide/network.md) in detail
- Explore [Advanced Examples](../examples/mesh-network.md)
- Try [Applying via SSH](../guide/ssh.md)
