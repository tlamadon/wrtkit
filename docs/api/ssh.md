# SSH API

SSH connection management for remote OpenWRT devices.

## SSHConnection

::: wrtkit.ssh.SSHConnection
    options:
      show_root_heading: true
      members:
        - __init__
        - connect
        - disconnect
        - execute
        - execute_uci_command
        - get_uci_config
        - commit_changes
        - reload_config

## Usage Example

```python
from wrtkit import SSHConnection

# Create connection
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    password="password"
)

# Connect
ssh.connect()

# Execute command
stdout, stderr, exit_code = ssh.execute("uci show network")

# Get UCI config
config = ssh.get_uci_config("network")

# Commit and reload
ssh.commit_changes()
ssh.reload_config()

# Disconnect
ssh.disconnect()

# Or use context manager
with SSHConnection(host="192.168.1.1", username="root", password="pass") as ssh:
    config = ssh.get_uci_config("network")
```

## See Also

- [SSH Guide](../guide/ssh.md)
- [API Overview](config.md)
