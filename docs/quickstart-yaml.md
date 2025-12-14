# YAML/JSON Quick Start Guide

Get started with YAML/JSON configuration in 5 minutes.

## Installation

```bash
pip install wrtkit
```

## Your First YAML Configuration

Create a file named `my-router.yaml`:

```yaml
network:
  devices:
    br_lan:
      name: br-lan
      type: bridge
      ports:
        - lan1
        - lan2
        - lan3
        - lan4

  interfaces:
    lan:
      device: br-lan
      proto: static
      ipaddr: 192.168.1.1
      netmask: 255.255.255.0

    wan:
      device: eth0
      proto: dhcp

wireless:
  radios:
    radio0:
      channel: 36
      htmode: HE80
      country: US

  interfaces:
    default_radio0:
      device: radio0
      mode: ap
      network: lan
      ssid: MyNetwork
      encryption: sae
      key: SecurePassword123!

dhcp:
  sections:
    lan:
      interface: lan
      start: 100
      limit: 150
      leasetime: 12h
```

## Load and Apply

```python
from wrtkit import UCIConfig, SSHConnection

# Load configuration from YAML
config = UCIConfig.from_yaml_file("my-router.yaml")

# Connect and apply
with SSHConnection("192.168.1.1", username="root", password="your-password") as ssh:
    # Preview changes
    diff = config.diff(ssh)
    print(diff.to_tree())

    # Apply if satisfied
    if not diff.is_empty():
        config.apply(ssh)
        print("✓ Configuration applied!")
```

## Build and Save

```python
from wrtkit import UCIConfig
from wrtkit.network import NetworkInterface

# Build configuration programmatically
config = UCIConfig()

lan = NetworkInterface("lan") \
    .with_device("br-lan") \
    .with_static_ip("192.168.1.1", "255.255.255.0")
config.network.add_interface(lan)

# Save to YAML
config.to_yaml_file("generated-config.yaml")

# Or save to JSON
config.to_json_file("generated-config.json")
```

## Hybrid Approach

```python
# Start with a YAML template
config = UCIConfig.from_yaml_file("base-config.yaml")

# Add dynamic configuration
for vlan_id in [10, 20, 30]:
    guest = NetworkInterface(f"guest{vlan_id}") \
        .with_device(f"lan1.{vlan_id}") \
        .with_static_ip(f"192.168.{vlan_id}.1", "255.255.255.0")
    config.network.add_interface(guest)

# Save combined result
config.to_yaml_file("final-config.yaml")
```

## Generate Schema for IDE

```python
from wrtkit import UCIConfig
import json

# Generate schema
schema = UCIConfig.json_schema()

# Save for IDE autocomplete
with open("uci-config.schema.json", "w") as f:
    json.dump(schema, f, indent=2)
```

Then configure your IDE (VS Code example):

```json
{
  "yaml.schemas": {
    "./uci-config.schema.json": "router-configs/*.yaml"
  }
}
```

## Next Steps

- [Full YAML/JSON Guide](yaml-json-guide.md) - Complete reference
- [Examples](../examples/) - Real-world examples
- [API Reference](../README.md) - Full API documentation

## Common Tasks

### Load Individual Section

```python
from wrtkit.network import NetworkInterface

# Load just one interface
lan = NetworkInterface.from_yaml_file("lan-interface.yaml", "lan")
```

### Merge Configurations

```python
config1 = UCIConfig.from_yaml_file("network-config.yaml")
config2 = UCIConfig.from_yaml_file("wireless-config.yaml")

# Create merged config
merged = UCIConfig()
for iface in config1.network.interfaces:
    merged.network.add_interface(iface)
for radio in config2.wireless.radios:
    merged.wireless.add_radio(radio)
```

### Validate Configuration

```python
config = UCIConfig.from_yaml_file("router.yaml")

# Generate UCI commands to validate
commands = config.get_all_commands()
print(f"Configuration generates {len(commands)} UCI commands")

# Check for specific settings
lan_interfaces = [i for i in config.network.interfaces if i._section == "lan"]
assert len(lan_interfaces) == 1, "LAN interface not found"
assert lan_interfaces[0].proto == "static", "LAN should use static IP"
```

## Troubleshooting

**Problem:** YAML won't load

**Solution:** Check YAML syntax using a validator:
```bash
python -c "import yaml; yaml.safe_load(open('my-router.yaml'))"
```

**Problem:** IDE doesn't show autocomplete

**Solution:** Make sure you've generated and configured the schema (see "Generate Schema" above)

**Problem:** Configuration doesn't match expectations

**Solution:** Export to YAML to inspect:
```python
config = UCIConfig.from_yaml_file("config.yaml")
print(config.to_yaml())
```

## Tips

- Use YAML for human-edited configs (supports comments, better readability)
- Use JSON for machine-generated configs (strict syntax, better for APIs)
- Commit YAML configs to git for version control
- Use `exclude_none=True` (default) to keep configs clean
- The schema is permissive - you can add custom UCI options
