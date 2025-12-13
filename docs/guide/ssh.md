# SSH Operations

Connect to and manage OpenWRT devices over SSH.

## Creating a Connection

### Password Authentication

```python
from wrtkit import SSHConnection

ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    password="your-password"
)
```

### Key-Based Authentication

```python
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    key_filename="/home/user/.ssh/id_rsa"
)
```

### Custom Port

```python
ssh = SSHConnection(
    host="192.168.1.1",
    port=2222,
    username="root",
    password="your-password",
    timeout=60
)
```

## Using Context Manager

Automatically handle connection lifecycle:

```python
with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
    # Connection is open here
    diff = config.diff(ssh)
    config.apply(ssh)
# Connection is automatically closed
```

## Connection Methods

### Execute Commands

```python
stdout, stderr, exit_code = ssh.execute("uci show network")
if exit_code == 0:
    print(stdout)
else:
    print(f"Error: {stderr}")
```

### Get UCI Configuration

```python
network_config = ssh.get_uci_config("network")
wireless_config = ssh.get_uci_config("wireless")
print(network_config)
```

### Commit Changes

```python
# Commit all changes
ssh.commit_changes()

# Commit specific packages
ssh.commit_changes(["network", "wireless"])
```

### Reload Configuration

```python
ssh.reload_config()  # Restart network and reload WiFi
```

## Configuration Comparison

### Get Differences

```python
diff = config.diff(ssh)

if diff.is_empty():
    print("No changes needed")
else:
    print("Changes to apply:")
    print(diff)
```

The diff shows:
- Commands to add (not in remote)
- Commands to remove (not in local)
- Commands to modify (different values)

## Applying Configuration

### Basic Apply

```python
config.apply(ssh)
```

### With Options

```python
config.apply(
    ssh,
    dry_run=False,       # Actually apply (True = preview only)
    auto_commit=True,    # Commit after applying
    auto_reload=True     # Reload services after commit
)
```

### Dry Run

Preview without applying:

```python
config.apply(ssh, dry_run=True)
```

Output shows all commands that would be executed.

### Manual Control

```python
# Apply without auto-commit
config.apply(ssh, auto_commit=False, auto_reload=False)

# Manually commit and reload
ssh.commit_changes()
ssh.reload_config()
```

## Complete Example

```python
from wrtkit import UCIConfig, SSHConnection

# Create configuration
config = UCIConfig()
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1") \
    .netmask("255.255.255.0")

# Connect and apply
with SSHConnection(
    host="192.168.1.1",
    username="root",
    key_filename="/home/user/.ssh/id_rsa"
) as ssh:
    # Check differences
    diff = config.diff(ssh)
    print("Proposed changes:")
    print(diff)

    # Confirm before applying
    if not diff.is_empty():
        response = input("Apply changes? (y/n): ")
        if response.lower() == 'y':
            config.apply(ssh)
            print("Configuration applied successfully!")
    else:
        print("No changes needed.")
```

## Error Handling

```python
from wrtkit import SSHConnection

try:
    ssh = SSHConnection(host="192.168.1.1", username="root", password="wrong")
    ssh.connect()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices

1. **Use SSH Keys**: More secure than passwords
2. **Use Context Manager**: Ensures connections are closed
3. **Check Diff First**: Always review changes before applying
4. **Use Dry Run**: Test complex configurations first
5. **Handle Errors**: Wrap SSH operations in try/except blocks

## See Also

- [Configuration Management](config-management.md) - Managing configurations
- [Quick Start](../getting-started/quick-start.md) - Getting started guide
- [API Reference](../api/ssh.md) - SSH API documentation
