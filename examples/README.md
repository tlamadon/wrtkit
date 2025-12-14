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
