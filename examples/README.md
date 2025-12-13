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
diff = config.diff(ssh)
print(diff)
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
