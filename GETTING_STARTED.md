# Getting Started with WRTKit

This guide will help you get started with WRTKit, a Python library for managing OpenWRT configuration.

## Installation

```bash
pip install wrtkit
```

For development:
```bash
git clone https://github.com/yourusername/wrtkit.git
cd wrtkit
pip install -e ".[dev]"
```

## Your First Configuration

Let's create a simple router configuration:

```python
from wrtkit import UCIConfig

# Create a new configuration
config = UCIConfig()

# Configure LAN interface
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

# Configure WAN interface
config.network.interface("wan") \
    .device("eth1") \
    .proto("dhcp")

# Print the generated UCI commands
print(config.to_script())
```

This will output:
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

## Connecting to a Remote Device

```python
from wrtkit import UCIConfig, SSHConnection

# Create your configuration
config = UCIConfig()
# ... configure your settings ...

# Connect via SSH
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    password="your-password"  # or use key_filename="/path/to/key"
)

# Check what will change
diff = config.diff(ssh)
print(diff)

# Apply if you're satisfied
config.apply(ssh)
```

## Common Patterns

### Bridge Configuration

```python
# Create a bridge with multiple ports
config.network.device("br_lan") \
    .name("br-lan") \
    .type("bridge") \
    .add_port("lan1") \
    .add_port("lan2") \
    .add_port("lan3")

# Use the bridge for the LAN interface
config.network.interface("lan") \
    .device("br-lan") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")
```

### Wireless Access Point

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
    .key("MySecurePassword")
```

### DHCP Server

```python
config.dhcp.dhcp("lan") \
    .interface("lan") \
    .start(100) \
    .limit(150) \
    .leasetime("12h")
```

### Firewall Rules

```python
# LAN zone
config.firewall.zone(0) \
    .name("lan") \
    .input("ACCEPT") \
    .output("ACCEPT") \
    .forward("ACCEPT") \
    .add_network("lan")

# WAN zone with masquerading
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

## Saving to File

```python
# Save as a shell script
config.save_to_file("my_router_config.sh")

# You can then copy this to your router and run:
# sh my_router_config.sh
```

## Advanced: Mesh Networking with BATMAN-ADV

```python
# Configure batman-adv interface
config.network.interface("bat0") \
    .proto("batadv") \
    .routing_algo("BATMAN_IV") \
    .gw_mode("server") \
    .gw_bandwidth("10000/10000")

# Create a mesh interface
config.wireless.wifi_iface("mesh0") \
    .device("radio1") \
    .mode("mesh") \
    .network("mesh0") \
    .mesh_id("my-mesh-network") \
    .encryption("sae") \
    .key("mesh-password") \
    .mesh_fwding(False)

# Link the mesh interface to batman-adv
config.network.interface("mesh0") \
    .proto("batadv_hardif") \
    .master("bat0")
```

## Next Steps

- Check out the [examples](examples/) directory for more complete configurations
- Read the [API documentation](README.md) for all available options
- See [CONTRIBUTING.md](CONTRIBUTING.md) if you want to add new features

## Troubleshooting

### Connection Issues

If you can't connect via SSH:
1. Make sure the router is accessible: `ping 192.168.1.1`
2. Verify SSH is enabled on the router
3. Check if you're using the correct username (usually `root`)
4. Try using an SSH key instead of a password

### Configuration Not Applied

If the configuration doesn't seem to apply:
1. Check the diff first: `diff = config.diff(ssh)`
2. Use dry run mode: `config.apply(ssh, dry_run=True)`
3. Look at the router logs: `ssh root@192.168.1.1 'logread'`
4. Make sure `auto_commit=True` and `auto_reload=True` when applying

### Import Errors

If you get import errors:
```python
# Make sure you have the package installed
pip install wrtkit

# For development
pip install -e ".[dev]"
```

## Getting Help

- [GitHub Issues](https://github.com/yourusername/wrtkit/issues)
- [Examples Directory](examples/)
- [Contributing Guide](CONTRIBUTING.md)
