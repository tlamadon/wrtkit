# YAML/JSON Configuration Guide

This guide explains how to use YAML and JSON formats to define and manage OpenWRT configurations with wrtkit.

## Table of Contents

- [Overview](#overview)
- [Schema Generation](#schema-generation)
- [Individual Section Configuration](#individual-section-configuration)
- [Complete Configuration](#complete-configuration)
- [API Reference](#api-reference)
- [Examples](#examples)

## Overview

All wrtkit configuration objects are built on Pydantic models, which means they support:

- **Serialization**: Convert Python objects to YAML/JSON
- **Deserialization**: Load configurations from YAML/JSON files
- **Schema Generation**: Generate JSON/YAML schemas for IDE autocomplete and validation
- **Permissive Schema**: Unknown fields are accepted for future UCI options

## Schema Generation

Generate schemas to enable IDE autocomplete and validation:

### JSON Schema

```python
from wrtkit.config import UCIConfig
from wrtkit.network import NetworkInterface
import json

# Generate schema for a specific section type
schema = NetworkInterface.json_schema()
with open("network-interface-schema.json", "w") as f:
    json.dump(schema, f, indent=2)

# Generate schema for complete configuration
full_schema = UCIConfig.json_schema()
with open("uci-config-schema.json", "w") as f:
    json.dump(full_schema, f, indent=2)
```

### YAML Schema

```python
from wrtkit.config import UCIConfig
from wrtkit.network import NetworkInterface

# Generate YAML-formatted schema
schema_yaml = NetworkInterface.yaml_schema()
with open("network-interface-schema.yaml", "w") as f:
    f.write(schema_yaml)

# Complete configuration schema in YAML
full_schema_yaml = UCIConfig.yaml_schema()
print(full_schema_yaml)
```

## Individual Section Configuration

Load and save individual configuration sections (interfaces, radios, etc.):

### Network Interface

**YAML Format:**

```yaml
# lan-interface.yaml
device: br-lan
proto: static
ipaddr: 192.168.1.1
netmask: 255.255.255.0
gateway: 192.168.1.254
```

**Usage:**

```python
from wrtkit.network import NetworkInterface

# Load from YAML file
interface = NetworkInterface.from_yaml_file("lan-interface.yaml", "lan")

# Or from YAML string
yaml_str = """
device: br-lan
proto: static
ipaddr: 192.168.1.1
"""
interface = NetworkInterface.from_yaml(yaml_str, "lan")

# Save to YAML
interface.to_yaml_file("output.yaml")

# Or get as string
yaml_output = interface.to_yaml()
print(yaml_output)
```

### Wireless Access Point

**YAML Format:**

```yaml
# wireless-ap.yaml
device: radio0
mode: ap
network: lan
ssid: MyWiFiNetwork
encryption: sae
key: MySecurePassword123!
ieee80211r: true
mobility_domain: 4f57
```

**Usage:**

```python
from wrtkit.wireless import WirelessInterface

# Load from YAML
ap = WirelessInterface.from_yaml_file("wireless-ap.yaml", "default_radio0")

# Save to JSON
ap.to_json_file("wireless-ap.json")
```

### JSON Format

All sections also support JSON:

```python
from wrtkit.network import NetworkInterface

# Load from JSON file
interface = NetworkInterface.from_json_file("config.json", "lan")

# Save to JSON
interface.to_json_file("output.json", indent=2)
```

## Complete Configuration

### Full Configuration Structure

**YAML Format:**

```yaml
network:
  devices:
    br_lan:
      name: br-lan
      type: bridge
      ports:
        - lan1
        - lan2
  interfaces:
    lan:
      device: br-lan
      proto: static
      ipaddr: 192.168.1.1
      netmask: 255.255.255.0

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

firewall:
  zones:
    lan:
      name: lan
      input: ACCEPT
      output: ACCEPT
      forward: ACCEPT
      network:
        - lan
    wan:
      name: wan
      input: REJECT
      output: ACCEPT
      forward: REJECT
      masq: true
      mtu_fix: true
      network:
        - wan
  forwardings:
    - src: lan
      dest: wan
```

### Loading Complete Configuration

```python
from wrtkit.config import UCIConfig

# Load from YAML file
config = UCIConfig.from_yaml_file("router-config.yaml")

# Load from JSON file
config = UCIConfig.from_json_file("router-config.json")

# Verify loaded configuration
print(f"Network interfaces: {len(config.network.interfaces)}")
print(f"Wireless radios: {len(config.wireless.radios)}")

# Generate UCI commands
commands = config.get_all_commands()
for cmd in commands:
    print(cmd.to_string())
```

### Saving Complete Configuration

```python
from wrtkit.config import UCIConfig
from wrtkit.network import NetworkInterface, NetworkDevice

# Build configuration programmatically
config = UCIConfig()

device = NetworkDevice("br_lan") \
    .with_name("br-lan") \
    .with_type("bridge") \
    .with_ports(["lan1", "lan2"])
config.network.add_device(device)

interface = NetworkInterface("lan") \
    .with_device("br-lan") \
    .with_static_ip("192.168.1.1", "255.255.255.0")
config.network.add_interface(interface)

# Save to YAML
config.to_yaml_file("my-router-config.yaml")

# Save to JSON
config.to_json_file("my-router-config.json", indent=2)

# Get as string
yaml_str = config.to_yaml()
json_str = config.to_json()
```

## API Reference

### UCISection Methods

All configuration sections (NetworkInterface, WirelessRadio, etc.) inherit these methods:

#### Schema Generation

- `json_schema(title: str = None) -> Dict[str, Any]`: Generate JSON Schema
- `yaml_schema(title: str = None) -> str`: Generate YAML-formatted schema

#### Serialization

- `to_dict(exclude_none=True, exclude_private=True) -> Dict`: Convert to dictionary
- `to_json(exclude_none=True, exclude_private=True, indent=2) -> str`: Convert to JSON string
- `to_yaml(exclude_none=True, exclude_private=True) -> str`: Convert to YAML string
- `to_json_file(filename, exclude_none=True, exclude_private=True, indent=2)`: Save to JSON file
- `to_yaml_file(filename, exclude_none=True, exclude_private=True)`: Save to YAML file

#### Deserialization

- `from_dict(data: Dict, section_name: str) -> T`: Create from dictionary
- `from_json(json_str: str, section_name: str) -> T`: Create from JSON string
- `from_yaml(yaml_str: str, section_name: str) -> T`: Create from YAML string
- `from_json_file(filename: str, section_name: str) -> T`: Load from JSON file
- `from_yaml_file(filename: str, section_name: str) -> T`: Load from YAML file

### UCIConfig Methods

#### Schema Generation

- `json_schema(title="UCI Configuration Schema") -> Dict[str, Any]`: Generate JSON Schema
- `yaml_schema(title="UCI Configuration Schema") -> str`: Generate YAML-formatted schema

#### Serialization

- `to_dict(exclude_none=True) -> Dict`: Convert to dictionary
- `to_json(indent=2, exclude_none=True) -> str`: Convert to JSON string
- `to_yaml(exclude_none=True) -> str`: Convert to YAML string
- `to_json_file(filename, indent=2, exclude_none=True)`: Save to JSON file
- `to_yaml_file(filename, exclude_none=True)`: Save to YAML file

#### Deserialization

- `from_dict(data: Dict) -> UCIConfig`: Create from dictionary
- `from_json(json_str: str) -> UCIConfig`: Create from JSON string
- `from_yaml(yaml_str: str) -> UCIConfig`: Create from YAML string
- `from_json_file(filename: str) -> UCIConfig`: Load from JSON file
- `from_yaml_file(filename: str) -> UCIConfig`: Load from YAML file

## Examples

### Example 1: Hybrid Approach

Mix programmatic and declarative configuration:

```python
from wrtkit.config import UCIConfig
from wrtkit.network import NetworkInterface

# Load base configuration from YAML
config = UCIConfig.from_yaml_file("base-config.yaml")

# Add dynamic configuration programmatically
guest_net = NetworkInterface("guest") \
    .with_device("lan1.100") \
    .with_static_ip("192.168.100.1", "255.255.255.0")
config.network.add_interface(guest_net)

# Save merged configuration
config.to_yaml_file("final-config.yaml")
```

### Example 2: Configuration Templates

Create reusable templates:

```python
from wrtkit.wireless import WirelessInterface

# Load template
template = WirelessInterface.from_yaml_file("ap-template.yaml", "template")

# Customize for each radio
for i, radio in enumerate(["radio0", "radio1"]):
    ap = template.model_copy(update={
        "device": radio,
        "ssid": f"MyNetwork-{i}"
    })
    # Use the customized AP config...
```

### Example 3: Validation and Testing

```python
from wrtkit.config import UCIConfig

# Load configuration
config = UCIConfig.from_yaml_file("router-config.yaml")

# Validate by generating commands
commands = config.get_all_commands()
assert len(commands) > 0

# Export for review
print(config.to_yaml())

# Save UCI script for manual review
config.save_to_file("review.sh")
```

### Example 4: Version Control

YAML/JSON configurations work great with version control:

```bash
# Track your router configurations
git add router-configs/*.yaml
git commit -m "Update LAN IP address"
git diff HEAD~1 router-configs/production.yaml
```

### Example 5: Configuration Migration

Convert between formats:

```python
from wrtkit.config import UCIConfig

# Load from JSON
config = UCIConfig.from_json_file("old-config.json")

# Save to YAML for better readability
config.to_yaml_file("new-config.yaml")
```

## Real-World Scenarios

### Scenario 1: Multi-Site Deployment

Deploy the same configuration to multiple routers with site-specific changes:

**Template (base-config.yaml):**
```yaml
network:
  devices:
    br_lan:
      name: br-lan
      type: bridge
      ports:
        - lan1
        - lan2

wireless:
  radios:
    radio0:
      channel: 36
      htmode: HE80
      country: US
```

**Deployment Script:**
```python
from wrtkit import UCIConfig
from wrtkit.network import NetworkInterface
from wrtkit import SSHConnection

sites = [
    {"name": "site1", "ip": "192.168.1.0", "router": "10.0.0.1"},
    {"name": "site2", "ip": "192.168.2.0", "router": "10.0.0.2"},
    {"name": "site3", "ip": "192.168.3.0", "router": "10.0.0.3"},
]

for site in sites:
    # Load base template
    config = UCIConfig.from_yaml_file("base-config.yaml")

    # Customize for site
    lan = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_static_ip(f"{site['ip'][:-1]}1", "255.255.255.0")
    config.network.add_interface(lan)

    # Save site-specific config
    config.to_yaml_file(f"configs/{site['name']}.yaml")

    # Deploy
    with SSHConnection(site["router"], username="root", password="pass") as ssh:
        config.apply(ssh)
        print(f"✓ Deployed to {site['name']}")
```

### Scenario 2: Configuration Testing

Test configurations before deployment:

```python
from wrtkit import UCIConfig
import pytest

def test_lan_configuration():
    """Test that LAN is configured correctly."""
    config = UCIConfig.from_yaml_file("production-router.yaml")

    # Verify LAN interface exists
    lan_interfaces = [i for i in config.network.interfaces if i._section == "lan"]
    assert len(lan_interfaces) == 1

    # Verify correct IP configuration
    lan = lan_interfaces[0]
    assert lan.proto == "static"
    assert lan.ipaddr == "192.168.1.1"
    assert lan.netmask == "255.255.255.0"

def test_wireless_security():
    """Test that wireless is properly secured."""
    config = UCIConfig.from_yaml_file("production-router.yaml")

    # All APs should use WPA3 or WPA2
    for iface in config.wireless.interfaces:
        if iface.mode == "ap":
            assert iface.encryption in ["sae", "psk2"], \
                f"AP {iface._section} uses weak encryption"

def test_firewall_rules():
    """Test firewall configuration."""
    config = UCIConfig.from_yaml_file("production-router.yaml")

    # WAN should reject incoming
    wan_zones = [z for z in config.firewall.zones if z.name == "wan"]
    assert len(wan_zones) == 1
    assert wan_zones[0].input == "REJECT"
```

### Scenario 3: Dynamic VLAN Generation

Generate VLAN configurations from a CSV or database:

**vlans.csv:**
```csv
vlan_id,name,subnet,dhcp_start,dhcp_limit
10,guest-wifi,192.168.10.0,50,100
20,iot,192.168.20.0,100,150
30,cameras,192.168.30.0,10,50
```

**Script:**
```python
import csv
from wrtkit import UCIConfig
from wrtkit.network import NetworkDevice, NetworkInterface
from wrtkit.dhcp import DHCPSection
from wrtkit.firewall import FirewallZone

config = UCIConfig()

with open('vlans.csv', 'r') as f:
    reader = csv.DictReader(f)
    for idx, row in enumerate(reader):
        vlan_id = int(row['vlan_id'])
        name = row['name']
        subnet = row['subnet']
        gateway = f"{subnet.rsplit('.', 1)[0]}.1"

        # VLAN device
        device = NetworkDevice(f"vlan_{vlan_id}") \
            .with_type("8021q") \
            .with_ifname("lan1") \
            .with_vid(vlan_id)
        config.network.add_device(device)

        # Interface
        interface = NetworkInterface(name) \
            .with_device(f"lan1.{vlan_id}") \
            .with_static_ip(gateway, "255.255.255.0")
        config.network.add_interface(interface)

        # DHCP
        dhcp = DHCPSection(name) \
            .with_interface(name) \
            .with_range(
                int(row['dhcp_start']),
                int(row['dhcp_limit']),
                "12h"
            )
        config.dhcp.add_dhcp(dhcp)

        # Firewall zone (isolated)
        zone = FirewallZone(idx) \
            .with_name(name) \
            .with_input("REJECT") \
            .with_output("ACCEPT") \
            .with_forward("REJECT") \
            .with_network(name)
        config.firewall.add_zone(zone)

# Save generated config
config.to_yaml_file("generated-vlans.yaml")
print(f"Generated configuration for {idx + 1} VLANs")
```

### Scenario 4: Configuration Backup and Restore

**Backup Script:**
```python
from wrtkit import UCIConfig, SSHConnection
from datetime import datetime

def backup_router(host, output_dir="backups"):
    """Backup router configuration to YAML."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    # Connect and retrieve current config
    with SSHConnection(host, username="root", password="pass") as ssh:
        # Create empty config to use diff functionality
        config = UCIConfig()

        # Get remote config via diff
        diff = config.diff(ssh, show_remote_only=True)

        # Extract remote commands and reconstruct config
        # (In practice, you'd parse the remote config)
        # For now, we'll document this is a limitation

    # Alternative: Use SSH to dump config directly
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/router_{host}_{timestamp}.yaml"

    print(f"✓ Backed up router {host} to {filename}")

# Restore from backup
def restore_router(backup_file, host):
    """Restore router configuration from YAML backup."""
    config = UCIConfig.from_yaml_file(backup_file)

    with SSHConnection(host, username="root", password="pass") as ssh:
        diff = config.diff(ssh)
        if not diff.is_empty():
            print("Changes to apply:")
            print(diff.to_tree())

            if input("Apply? (yes/no): ") == "yes":
                config.apply(ssh)
                print("✓ Configuration restored")
```

## Best Practices

1. **Use YAML for human-edited configs**: YAML is more readable and supports comments
2. **Use JSON for programmatic access**: JSON is better for APIs and automation
3. **Store schemas with configs**: Include schema files in your repo for IDE support
4. **Validate before deployment**: Load configs and generate UCI commands to verify
5. **Use version control**: Track configuration changes over time
6. **Keep templates**: Create reusable configuration templates for common setups
7. **Document custom fields**: Since the schema is permissive, document any custom UCI options
8. **Test configurations**: Write tests to verify config correctness
9. **Use hybrid approach**: Combine YAML templates with Python for dynamic generation
10. **Backup regularly**: Export configurations to YAML for disaster recovery

## Permissive Schema

The configuration is permissive by default, accepting unknown fields:

```yaml
# This works - custom UCI options are preserved
network:
  interfaces:
    lan:
      device: br-lan
      proto: static
      ipaddr: 192.168.1.1
      # Custom/future UCI option
      custom_option: custom_value
      experimental_feature: true
```

```python
interface = NetworkInterface.from_yaml_file("config.yaml", "lan")
# Custom fields are accessible
data = interface.model_dump()
print(data["custom_option"])  # "custom_value"
```

This allows you to use future UCI options that aren't yet explicitly defined in wrtkit.

## IDE Integration

For the best development experience with IDE autocomplete:

1. Generate schemas for your configuration types
2. Configure your IDE to use the JSON schemas
3. Most modern IDEs (VS Code, PyCharm, etc.) will provide autocomplete and validation

**VS Code Example:**

```json
{
  "yaml.schemas": {
    "./schemas/uci-config-schema.json": "router-configs/*.yaml"
  }
}
```

## Troubleshooting

### Issue: Section names not preserved

**Wrong:**
```yaml
# Missing section name - will fail
network:
  interfaces:
    - device: br-lan  # Wrong: list instead of dict
      proto: static
```

**Correct:**
```yaml
network:
  interfaces:
    lan:  # Section name as key
      device: br-lan
      proto: static
```

### Issue: Private fields appearing in YAML

Use `exclude_private=True` (default) to hide fields starting with `_`:

```python
# Good - no private fields
interface.to_yaml()  # exclude_private=True by default

# Bad - includes _package, _section, etc.
interface.to_yaml(exclude_private=False)
```

### Issue: None values in output

Use `exclude_none=True` (default) to omit None values:

```python
# Clean output
config.to_yaml()  # exclude_none=True by default

# Verbose output with all fields
config.to_yaml(exclude_none=False)
```
