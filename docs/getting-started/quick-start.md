# Quick Start

This guide will walk you through creating your first OpenWRT configuration with WRTKit.

## Basic Concepts

WRTKit uses a **builder pattern** that allows you to chain method calls to configure your OpenWRT device. The main components are:

- **UCIConfig** - The main configuration object
- **Network** - Network devices and interfaces
- **Wireless** - WiFi radios and interfaces
- **DHCP** - DHCP server settings
- **Firewall** - Firewall zones and rules
- **SSHConnection** - Connection to remote devices

## Your First Configuration

Let's create a simple router configuration:

```python
from wrtkit import UCIConfig

# Create a new configuration object
config = UCIConfig()

# Configure the LAN interface
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

# Configure the WAN interface
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")

# Print the generated configuration
print(config.to_script())
```

This generates:

```bash
#!/bin/sh

uci set network.lan='interface'
uci set network.lan.device='eth0'
uci set network.lan.proto='static'
uci set network.lan.ipaddr='192.168.1.1'
uci set network.lan.netmask='255.255.255.0'
uci set network.wan='interface'
uci set network.wan.device='eth1'
uci set network.wan.proto='dhcp'

uci commit
/etc/init.d/network restart
wifi reload
```

## Adding Wireless

Let's add a wireless access point:

```python
# Configure the radio
config.wireless.radio("radio0") \
    .channel(11) \
    .htmode("HT20") \
    .country("US") \
    .disabled(False)

# Create an access point
config.wireless.wifi_iface("default_ap") \
    .device("radio0") \
    .mode("ap") \
    .network("lan") \
    .ssid("MyNetwork") \
    .encryption("psk2") \
    .key("MySecurePassword123")
```

## Adding DHCP

Configure a DHCP server for the LAN:

```python
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")
```

## Adding Firewall Rules

Set up basic firewall zones:

```python
# LAN zone - permissive
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

# WAN zone - restrictive with NAT
config.firewall.zone(1) \
    .name("wan") \
    .input("REJECT") \
    .output("ACCEPT") \
    .forward("REJECT") \
    .masq(True) \
    .add_network("wan")

# Allow forwarding from LAN to WAN
config.firewall.forwarding(0) \
    .src("lan") \
    .dest("wan")
```

## Saving to a File

Save the configuration to a shell script:

```python
config.save_to_file("router_config.sh")
```

You can then copy this script to your router and execute it:

```bash
scp router_config.sh root@192.168.1.1:/tmp/
ssh root@192.168.1.1 'sh /tmp/router_config.sh'
```

## Applying via SSH

Or apply the configuration directly via SSH:

```python
from wrtkit import SSHConnection

# Connect to the router
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    password="your-password"
)

# Show what will change
diff = config.diff(ssh)
print("Changes to be applied:")
print(diff)

# Apply the configuration
if input("Apply? (y/n): ").lower() == 'y':
    config.apply(ssh, auto_commit=True, auto_reload=True)
    print("Configuration applied!")
```

## Using Context Manager

For automatic connection cleanup, use a context manager:

```python
with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
    diff = config.diff(ssh)
    if not diff.is_empty():
        config.apply(ssh)
```

## Complete Example

Here's a complete working example:

```python
from wrtkit import UCIConfig, SSHConnection

def create_basic_router():
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
        .country("US")

    config.wireless.wifi_iface("default_ap") \
        .device("radio0") \
        .mode("ap") \
        .network("lan") \
        .ssid("MyNetwork") \
        .encryption("psk2") \
        .key("MyPassword")

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

    return config

# Create and apply
config = create_basic_router()

# Option 1: Save to file
config.save_to_file("basic_router.sh")

# Option 2: Apply via SSH
# with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
#     config.apply(ssh)
```

## Next Steps

- Learn more about [Network Configuration](../guide/network.md)
- Explore [Wireless Configuration](../guide/wireless.md)
- See more [Examples](../examples/basic-router.md)
- Read the [API Reference](../api/config.md)
