# VLAN Configuration with YAML

This guide demonstrates how to configure VLANs on OpenWRT using YAML format with wrtkit.

## Why YAML?

YAML format offers several advantages for network configuration:
- **Human-readable** - Easy to understand and edit
- **Version control friendly** - Git diffs are meaningful
- **Templateable** - Easy to generate from scripts or tools
- **Shareable** - Configuration as code across teams
- **Less verbose** - More concise than Python code

## Basic YAML Structure

WRTkit YAML uses dictionaries where **keys are UCI section names**:

```yaml
network:
  devices:
    vlan10:              # UCI section name
      type: 8021q        # Device type
      ifname: eth0       # Parent interface
      vid: 10            # VLAN ID
      name: eth0.10      # Interface name

  interfaces:
    guest:               # UCI section name
      device: eth0.10    # Device to use
      proto: static      # Protocol
      ipaddr: 192.168.10.1
      netmask: 255.255.255.0
```

## Example Files

### 1. Basic 802.1Q VLANs
**File:** `vlan_basic.yaml`

Simple VLAN tagging on a single interface:
```bash
wrtkit preview vlan_basic.yaml
wrtkit apply vlan_basic.yaml
```

Creates:
- VLAN 10 on eth0 (192.168.10.0/24) - Guest network
- VLAN 20 on eth0 (192.168.20.0/24) - IoT network

### 2. Bridge VLAN Filtering
**File:** `vlan_bridge_filtering.yaml`

VLAN-aware bridge with access and trunk ports:
```bash
wrtkit preview vlan_bridge_filtering.yaml
wrtkit apply vlan_bridge_filtering.yaml
```

Port configuration:
- lan1, lan2: VLAN 10 untagged (access ports)
- lan3: VLAN 20 untagged (access port)
- lan4: VLANs 10+20 tagged (trunk port)

### 3. Inter-VLAN Routing
**File:** `vlan_inter_routing.yaml`

Router-on-a-stick with firewall rules:
```bash
wrtkit preview vlan_inter_routing.yaml
wrtkit apply vlan_inter_routing.yaml
```

Creates 4 VLANs with controlled routing between them.

## Port Tagging Reference

When configuring `bridge_vlans`, use these port tagging formats:

| Format | Description | Use Case |
|--------|-------------|----------|
| `port:t` | Tagged (trunk) | Carries tagged VLAN traffic |
| `port:u*` | Untagged + PVID (access) | Native VLAN for untagged devices |
| `port:*` | Tagged only, no PVID | Only accepts tagged traffic |
| `port:u` | Untagged only | Allows untagged traffic |

Example:
```yaml
bridge_vlans:
  vlan10:
    device: br-trunk
    vlan: 10
    ports:
      - lan1:u*  # Access port for PCs
      - lan2:u*  # Access port for printers
      - lan4:t   # Trunk port to switch
```

## Working with YAML in Python

### Load and Preview

```python
from wrtkit.config import UCIConfig
from wrtkit.ssh import SSHConnection

# Load from YAML file
config = UCIConfig.from_yaml_file("vlan_basic.yaml")

# Preview changes
with SSHConnection(host="192.168.1.1", username="root") as ssh:
    diff = config.diff(ssh)
    print(diff.to_tree())

    # Apply if desired
    if input("Apply? (y/n): ") == "y":
        config.apply(ssh)
```

### Load from String

```python
yaml_config = """
network:
  devices:
    vlan10:
      type: 8021q
      ifname: eth0
      vid: 10
      name: eth0.10
"""

config = UCIConfig.from_yaml(yaml_config)
```

### Create in Python, Export to YAML

```python
from wrtkit.config import UCIConfig
from wrtkit.network import NetworkDevice, NetworkInterface, NetworkConfig

# Create configuration
net = NetworkConfig()

vlan10 = (
    NetworkDevice("vlan10")
    .with_type("8021q")
    .with_ifname("eth0")
    .with_vid(10)
    .with_name("eth0.10")
)
net.add_device(vlan10)

iface = (
    NetworkInterface("guest")
    .with_device("eth0.10")
    .with_static_ip("192.168.10.1", "255.255.255.0")
)
net.add_interface(iface)

# Create UCI config and export
config = UCIConfig()
config.network = net

# Export to YAML
yaml_output = config.to_yaml()
print(yaml_output)

# Save to file
config.to_yaml_file("my_vlan_config.yaml")
```

### Modify Existing YAML

```python
# Load existing config
config = UCIConfig.from_yaml_file("vlan_basic.yaml")

# Modify in Python
from wrtkit.network import NetworkDevice, NetworkInterface

# Add another VLAN
vlan30 = (
    NetworkDevice("vlan30")
    .with_type("8021q")
    .with_ifname("eth0")
    .with_vid(30)
    .with_name("eth0.30")
)
config.network.add_device(vlan30)

cameras_iface = (
    NetworkInterface("cameras")
    .with_device("eth0.30")
    .with_static_ip("192.168.30.1", "255.255.255.0")
)
config.network.add_interface(cameras_iface)

# Save back to YAML
config.to_yaml_file("vlan_modified.yaml")
```

## Complete Example with DHCP

```yaml
network:
  devices:
    vlan10:
      type: 8021q
      ifname: eth0
      vid: 10
      name: eth0.10

  interfaces:
    guest:
      device: eth0.10
      proto: static
      ipaddr: 192.168.10.1
      netmask: 255.255.255.0

dhcp:
  sections:
    guest:
      interface: guest
      start: 100
      limit: 150
      leasetime: 12h
      dhcp_option:
        - 6,192.168.10.1  # DNS server

  hosts:
    printer:
      name: printer
      mac: "AA:BB:CC:DD:EE:FF"
      ip: 192.168.10.50
      leasetime: infinite
```

## VLAN Configuration Patterns

### Pattern 1: Guest Network Isolation

```yaml
network:
  devices:
    vlan_guest:
      type: 8021q
      ifname: eth0
      vid: 99
      name: eth0.99

  interfaces:
    guest:
      device: eth0.99
      proto: static
      ipaddr: 192.168.99.1
      netmask: 255.255.255.0

firewall:
  zones:
    zone_guest:
      name: guest
      network:
        - guest
      input: REJECT
      output: ACCEPT
      forward: REJECT  # No inter-client communication
```

### Pattern 2: IoT Device Segmentation

```yaml
network:
  devices:
    vlan_iot:
      type: 8021q
      ifname: eth0
      vid: 20
      name: eth0.20

  interfaces:
    iot:
      device: eth0.20
      proto: static
      ipaddr: 192.168.20.1
      netmask: 255.255.255.0

dhcp:
  hosts:
    camera1:
      mac: "00:11:22:33:44:55"
      ip: 192.168.20.10

    thermostat:
      mac: "00:11:22:33:44:66"
      ip: 192.168.20.11
```

### Pattern 3: Management VLAN

```yaml
network:
  devices:
    vlan_mgmt:
      type: 8021q
      ifname: eth0
      vid: 1
      name: eth0.1

  interfaces:
    management:
      device: eth0.1
      proto: static
      ipaddr: 192.168.1.1
      netmask: 255.255.255.0

firewall:
  zones:
    zone_mgmt:
      name: management
      network:
        - management
      input: ACCEPT
      output: ACCEPT
      forward: ACCEPT  # Can access all networks
```

## Tips and Best Practices

### 1. VLAN ID Ranges
- **1-99**: Management and infrastructure
- **100-199**: User networks (office, departments)
- **200-299**: Guest and temporary
- **300-399**: IoT and automation
- **400-4094**: Specialized services

### 2. Naming Conventions
- **Devices**: `vlan{id}` or `vlan_{purpose}`
- **Interfaces**: Descriptive names (`guest`, `iot`, `cameras`)
- **Bridge VLANs**: `vlan{id}` or descriptive

### 3. Documentation
- Always add comments explaining VLAN purpose
- Document port tagging for bridge VLANs
- Include network topology diagrams in comments

### 4. Version Control
```bash
# Track your YAML configs in git
git add vlans/*.yaml
git commit -m "Add guest network VLAN 99"

# Review changes before applying
wrtkit preview vlan_config.yaml
git diff vlan_config.yaml
```

### 5. Testing
```bash
# Always preview first
wrtkit preview my_vlan.yaml

# Use dry-run mode
python -c "
from wrtkit.config import UCIConfig
from wrtkit.ssh import SSHConnection

config = UCIConfig.from_yaml_file('my_vlan.yaml')
with SSHConnection(host='192.168.1.1', username='root') as ssh:
    config.apply(ssh, dry_run=True)
"
```

## Common VLAN Scenarios

### Scenario 1: Home Network with Guest WiFi
```yaml
network:
  devices:
    vlan_home:
      type: 8021q
      ifname: eth0
      vid: 10
      name: eth0.10

    vlan_guest:
      type: 8021q
      ifname: eth0
      vid: 20
      name: eth0.20

  interfaces:
    home:
      device: eth0.10
      proto: static
      ipaddr: 192.168.10.1
      netmask: 255.255.255.0

    guest:
      device: eth0.20
      proto: static
      ipaddr: 192.168.20.1
      netmask: 255.255.255.0
```

### Scenario 2: Small Office with Departments
```yaml
network:
  devices:
    vlan_admin:
      type: 8021q
      ifname: eth0
      vid: 10
      name: eth0.10

    vlan_sales:
      type: 8021q
      ifname: eth0
      vid: 20
      name: eth0.20

    vlan_dev:
      type: 8021q
      ifname: eth0
      vid: 30
      name: eth0.30
```

### Scenario 3: Lab Environment with Isolated Ports
See `vlan_bridge_filtering.yaml` for complete example.

## Troubleshooting

### YAML Loading Errors
```python
# Check YAML syntax
from wrtkit.config import UCIConfig
try:
    config = UCIConfig.from_yaml_file("my_config.yaml")
except Exception as e:
    print(f"Error: {e}")
```

### Validate Configuration
```python
# Get schema
schema = UCIConfig.yaml_schema()
print(schema)

# View generated UCI commands
config = UCIConfig.from_yaml_file("my_config.yaml")
for cmd in config.get_all_commands():
    print(cmd)
```

## Further Reading

- [OpenWRT VLAN Documentation](https://openwrt.org/docs/guide-user/network/vlan/)
- [Bridge VLAN Filtering](https://openwrt.org/docs/guide-user/network/vlan/switch_configuration)
- [802.1Q Standard](https://en.wikipedia.org/wiki/IEEE_802.1Q)
- Python examples: `vlan_example.py`

## Complete Examples

All example YAML files:
- `vlan_basic.yaml` - Basic 802.1Q VLANs
- `vlan_bridge_filtering.yaml` - Bridge VLAN filtering
- `vlan_inter_routing.yaml` - Inter-VLAN routing with firewall

For more Python examples, see:
- `vlan_example.py` - Comprehensive Python examples
