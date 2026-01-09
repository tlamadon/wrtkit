# WRTKit Examples

This directory contains examples demonstrating various use cases for wrtkit.

## Examples

### simple_example.py

A basic example showing how to:
- Configure network interfaces (LAN and WAN)
- Set up a DHCP server
- Configure a wireless access point
- Define basic firewall rules
- Generate and save UCI configuration scripts

Run with:
```bash
python examples/simple_example.py
```

### router_config.py

A comprehensive example that mirrors the `uci/router.cfg` configuration, demonstrating:
- LAN bridge configuration with multiple ports
- WAN interface setup
- DHCP server configuration
- Firewall zones and forwarding rules
- BATMAN-ADV mesh networking setup
- Multiple wireless radios and interfaces
- 802.11r fast roaming configuration
- Mesh networking with SAE encryption

Run with:
```bash
python examples/router_config.py
```

### diff_demo.py

An interactive demonstration of the enhanced diff functionality, showing:
- Linear vs tree-structured diff output formats
- Tracking remote-only UCI settings (not managed by your config)
- Hierarchical grouping by package and resource type
- Different types of changes: add, modify, and remote-only
- How to interpret diff symbols: `+`, `~`, and `*`

Run with:
```bash
python examples/diff_demo.py
```

### serial_example.py

Demonstrates how to use WRTKit with a serial console connection instead of SSH:
- Connecting to OpenWRT via serial port (e.g., /dev/ttyUSB0)
- Compatible with picocom, minicom, and other serial console tools
- Performing diff and apply operations over serial
- Handling login prompts and shell detection
- Connection troubleshooting tips

Run with:
```bash
python examples/serial_example.py

# Or test connection only:
python examples/serial_example.py test
```

**Note:** Make sure no other program is using the serial port, and you have permission to access it (add your user to the `dialout` group on Linux).

### vlan_example.py

Comprehensive VLAN configuration examples in **Python**, demonstrating:
- Basic 802.1Q VLAN tagging on single interfaces
- Bridge VLAN filtering for managed switches
- VLAN trunk ports with multiple VLANs
- Mixed tagged and untagged VLAN traffic
- Inter-VLAN routing (router-on-a-stick)
- VLANs on batman-adv mesh interfaces
- Port-based VLAN isolation

Run with:
```bash
python examples/vlan_example.py
```

This example shows six different VLAN scenarios:
1. **Basic 802.1Q VLANs** - Create tagged VLANs on a single interface
2. **Bridge VLAN Filtering** - Configure VLAN-aware bridges with access and trunk ports
3. **Multiple VLANs on Trunk** - Carry multiple VLANs over a single trunk port
4. **VLANs on batman-adv** - Network segmentation in mesh networks
5. **Port-based Isolation** - Isolate each physical port to its own VLAN
6. **Inter-VLAN Routing** - Enable routing between VLANs

**Port tagging reference:**
- `port:t` - Tagged (trunk port)
- `port:u*` - Untagged and PVID (access port)
- `port:*` - Tagged only, no PVID
- `port:u` - Untagged only

### VLAN_YAML_GUIDE.md + YAML Examples

**Comprehensive guide** for VLAN configuration using **YAML format**. YAML is more concise and easier to manage than Python code for configuration-as-code workflows.

**YAML Example Files:**
- `vlan_basic.yaml` - Basic 802.1Q VLANs
- `vlan_bridge_filtering.yaml` - Bridge VLAN with access/trunk ports
- `vlan_inter_routing.yaml` - Inter-VLAN routing with firewall

**Features:**
- Human-readable configuration format
- Version control friendly
- Easy to template and share
- Complete examples with DHCP and firewall
- Port tagging reference and best practices

Read the guide:
```bash
cat examples/VLAN_YAML_GUIDE.md
```

Use YAML configs:
```bash
wrtkit preview examples/vlan_basic.yaml
wrtkit apply examples/vlan_basic.yaml
```

Or in Python:
```python
from wrtkit.config import UCIConfig

config = UCIConfig.from_yaml_file("examples/vlan_basic.yaml")
# Preview, modify, or apply
```

### whitelist_example.py

Demonstrates the remote policy whitelist feature for managing router configurations:
- Whitelisting specific remote settings to keep
- Pattern matching with wildcards
- Combining with allowed_sections for backwards compatibility
- Practical use cases for preserving device-specific settings

Run with:
```bash
python examples/whitelist_example.py
```

## Usage Patterns

### 1. Generate Configuration Scripts

```python
from wrtkit import UCIConfig

config = UCIConfig()
# ... configure your settings ...
config.save_to_file("my_config.sh")
```

### 2. Compare with Remote Configuration

```python
from wrtkit import UCIConfig, SSHConnection

config = UCIConfig()
# ... configure your settings ...

ssh = SSHConnection(host="192.168.1.1", username="root", password="secret")

# Linear format (default)
diff = config.diff(ssh)
print(str(diff))

# Tree format (grouped by package and resource)
print(diff.to_tree())

# Control remote-only setting tracking
diff = config.diff(ssh, show_remote_only=True)  # Track unmanaged settings (default)
diff = config.diff(ssh, show_remote_only=False)  # Treat as settings to remove
```

### 3. Apply Configuration to Remote Device

```python
from wrtkit import UCIConfig, SSHConnection

config = UCIConfig()
# ... configure your settings ...

with SSHConnection(host="192.168.1.1", username="root", password="secret") as ssh:
    # Show what will change
    diff = config.diff(ssh)
    print(diff)

    # Apply the configuration
    if input("Apply? (y/n): ") == "y":
        config.apply(ssh, auto_commit=True, auto_reload=True)
```

### 4. Dry Run Mode

```python
# See what would be executed without actually applying
config.apply(ssh, dry_run=True)
```

## Builder Pattern

All configuration objects use a fluent builder pattern for easy configuration:

```python
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")
```

This is equivalent to:
```bash
uci set network.lan=interface
uci set network.lan.device='eth0'
uci set network.lan.proto='static'
uci set network.lan.ipaddr='192.168.1.1'
uci set network.lan.netmask='255.255.255.0'
```

## SSH Connection Options

### Using Password

```python
ssh = SSHConnection(host="192.168.1.1", username="root", password="secret")
```

### Using SSH Key

```python
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    key_filename="/home/user/.ssh/id_rsa"
)
```

### With Custom Port and Timeout

```python
ssh = SSHConnection(
    host="192.168.1.1",
    port=2222,
    username="root",
    password="secret",
    timeout=60
)
```
