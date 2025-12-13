# Configuration Management

Learn how to create, export, and manage UCI configurations.

## Creating Configurations

### Initialize

```python
from wrtkit import UCIConfig

config = UCIConfig()
```

The `UCIConfig` object provides access to:
- `config.network` - Network configuration
- `config.wireless` - Wireless configuration
- `config.dhcp` - DHCP configuration
- `config.firewall` - Firewall configuration

### Building Configuration

Use the builder pattern:

```python
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1")
```

Each method returns `self`, allowing chaining.

## Exporting Configurations

### Generate Script

```python
script = config.to_script()
print(script)
```

Options:

```python
script = config.to_script(
    include_commit=True,   # Include 'uci commit'
    include_reload=True    # Include service reload commands
)
```

### Save to File

```python
config.save_to_file("my_config.sh")
```

With options:

```python
config.save_to_file(
    "my_config.sh",
    include_commit=True,
    include_reload=True
)
```

### Get Command List

```python
commands = config.get_all_commands()
for cmd in commands:
    print(cmd.to_string())
```

## Configuration Templates

### Create Reusable Templates

```python
def basic_router_template(lan_ip="192.168.1.1", ssid="MyNetwork", password=""):
    config = UCIConfig()

    config.network.interface("lan") \
        .device("eth0") \
        .proto("static") \
        .ipaddr(lan_ip) \
        .netmask("255.255.255.0")

    config.network.interface("wan") \
        .device("eth1") \
        .proto("dhcp")

    config.wireless.radio("radio0") \
        .channel(11) \
        .htmode("HT20") \
        .country("US")

    config.wireless.wifi_iface("default_ap") \
        .device("radio0") \
        .mode("ap") \
        .network("lan") \
        .ssid(ssid) \
        .encryption("psk2") \
        .key(password)

    config.dhcp.dhcp("lan") \
        .interface("lan") \
        .start(100) \
        .limit(150) \
        .leasetime("12h")

    return config

# Use the template
config = basic_router_template(
    lan_ip="192.168.10.1",
    ssid="HomeNetwork",
    password="SecurePass123"
)
```

## Modular Configuration

### Separate Concerns

```python
def configure_network(config, lan_ip):
    config.network.interface("lan") \
        .device("eth0") \
        .proto("static") \
        .ipaddr(lan_ip) \
        .netmask("255.255.255.0")

    config.network.interface("wan") \
        .device("eth1") \
        .proto("dhcp")

def configure_wireless(config, ssid, password):
    config.wireless.radio("radio0") \
        .channel(11) \
        .country("US")

    config.wireless.wifi_iface("default_ap") \
        .device("radio0") \
        .mode("ap") \
        .network("lan") \
        .ssid(ssid) \
        .encryption("psk2") \
        .key(password)

def configure_firewall(config):
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

# Build complete configuration
config = UCIConfig()
configure_network(config, "192.168.1.1")
configure_wireless(config, "MyNetwork", "password")
configure_firewall(config)
```

## Configuration from Files

### Load Settings from JSON

```python
import json

# Load settings
with open("router_settings.json") as f:
    settings = json.load(f)

# Build configuration
config = UCIConfig()

# Network
config.network.interface("lan") \
    .device(settings["lan"]["device"]) \
    .proto("static") \
    .ipaddr(settings["lan"]["ip"]) \
    .netmask(settings["lan"]["netmask"])

# Wireless
config.wireless.wifi_iface("ap") \
    .device("radio0") \
    .mode("ap") \
    .ssid(settings["wifi"]["ssid"]) \
    .encryption("psk2") \
    .key(settings["wifi"]["password"])
```

Example `router_settings.json`:

```json
{
  "lan": {
    "device": "eth0",
    "ip": "192.168.1.1",
    "netmask": "255.255.255.0"
  },
  "wifi": {
    "ssid": "MyNetwork",
    "password": "SecurePassword123"
  }
}
```

## Version Control

Store configurations in git:

```python
# generate_config.py
from wrtkit import UCIConfig

config = UCIConfig()
# ... build configuration ...

config.save_to_file("configs/production.sh")
```

Then use git:

```bash
git add configs/production.sh
git commit -m "Update production router config"
git push
```

## Deployment Workflow

```python
from wrtkit import UCIConfig, SSHConnection

def deploy_config(config_func, host, **kwargs):
    """Deploy a configuration to a router."""
    # Generate config
    config = config_func(**kwargs)

    # Connect
    with SSHConnection(host=host, username="root", **kwargs.get("ssh", {})) as ssh:
        # Show diff
        diff = config.diff(ssh)
        print(f"\nChanges for {host}:")
        print(diff)

        # Apply
        if not diff.is_empty():
            response = input(f"Apply to {host}? (y/n): ")
            if response.lower() == 'y':
                config.apply(ssh)
                print(f"✓ Applied to {host}")
        else:
            print(f"✓ {host} up to date")

# Deploy to multiple routers
deploy_config(
    basic_router_template,
    host="192.168.1.1",
    lan_ip="192.168.1.1",
    ssid="Router1",
    password="pass1"
)

deploy_config(
    basic_router_template,
    host="192.168.2.1",
    lan_ip="192.168.2.1",
    ssid="Router2",
    password="pass2"
)
```

## See Also

- [SSH Operations](ssh.md) - Working with remote devices
- [Examples](../examples/basic-router.md) - Complete examples
- [API Reference](../api/config.md) - Configuration API
