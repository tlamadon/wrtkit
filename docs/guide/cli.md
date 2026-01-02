# Command Line Interface

WRTKit provides a command-line interface (`wrtkit`) for managing OpenWRT device configurations directly from your terminal.

## Installation

The CLI is included when you install WRTKit:

```bash
pip install wrtkit
```

After installation, the `wrtkit` command will be available in your terminal.

## Quick Start

```bash
# Validate a configuration file
wrtkit validate config.yaml

# Preview changes (compare config with device)
wrtkit preview config.yaml 192.168.1.1

# Apply changes with dry-run first
wrtkit apply config.yaml 192.168.1.1 --dry-run

# Apply changes for real
wrtkit apply config.yaml 192.168.1.1 -p mypassword
```

## Commands

### `wrtkit preview`

Compare a local configuration file with the current state of a remote device. This shows what changes would be made without actually applying them.

```bash
wrtkit preview CONFIG_FILE TARGET [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `CONFIG_FILE` | Path to a YAML or JSON configuration file |
| `TARGET` | Device to compare against (IP, hostname, or serial port) |

**Options:**

| Option | Description |
|--------|-------------|
| `-p, --password TEXT` | SSH/login password |
| `-k, --key-file PATH` | SSH private key file |
| `-t, --timeout INTEGER` | Connection timeout in seconds (default: 30) |
| `--show-commands` | Show UCI commands that would be executed |
| `--no-color` | Disable colored output |
| `--tree` | Show diff as tree (default) |
| `--linear` | Show diff as linear list |

**Examples:**

```bash
# Basic preview
wrtkit preview config.yaml 192.168.1.1

# Preview with password authentication
wrtkit preview config.yaml router.local -p mysecretpassword

# Preview with SSH key
wrtkit preview config.yaml 192.168.1.1 -k ~/.ssh/id_rsa

# Show the UCI commands that would be run
wrtkit preview config.yaml 192.168.1.1 --show-commands

# Preview via serial connection
wrtkit preview config.yaml /dev/ttyUSB0 -p password
```

### `wrtkit apply`

Apply a configuration to a remote device. By default, this will show the diff and ask for confirmation before making changes.

```bash
wrtkit apply CONFIG_FILE TARGET [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `CONFIG_FILE` | Path to a YAML or JSON configuration file |
| `TARGET` | Device to configure (IP, hostname, or serial port) |

**Options:**

| Option | Description |
|--------|-------------|
| `-p, --password TEXT` | SSH/login password |
| `-k, --key-file PATH` | SSH private key file |
| `-t, --timeout INTEGER` | Connection timeout in seconds (default: 30) |
| `--dry-run` | Show what would be done without making changes |
| `--show-commands` | Show UCI commands that would be executed |
| `--no-commit` | Don't commit changes after applying |
| `--no-reload` | Don't reload services after applying |
| `--remove-unmanaged` | Remove settings on device not in config (dangerous!) |
| `--no-color` | Disable colored output |
| `-y, --yes` | Skip confirmation prompt |

**Examples:**

```bash
# Dry run - see what would happen
wrtkit apply config.yaml 192.168.1.1 --dry-run

# Dry run with UCI commands shown
wrtkit apply config.yaml 192.168.1.1 --dry-run --show-commands

# Apply with confirmation prompt
wrtkit apply config.yaml 192.168.1.1 -p password

# Apply without confirmation (useful for scripts)
wrtkit apply config.yaml router.local -y

# Apply but don't reload services (manual reload later)
wrtkit apply config.yaml 192.168.1.1 --no-reload

# Apply via serial connection
wrtkit apply config.yaml /dev/ttyUSB0
```

!!! warning "Using `--remove-unmanaged`"
    The `--remove-unmanaged` flag will delete any UCI settings on the device that are not defined in your configuration file. This can be dangerous if your config file is incomplete. Always do a `--dry-run` first to see what would be removed.

### `wrtkit validate`

Validate a configuration file without connecting to any device. Useful for checking syntax and structure before deployment.

```bash
wrtkit validate CONFIG_FILE [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `CONFIG_FILE` | Path to a YAML or JSON configuration file |

**Options:**

| Option | Description |
|--------|-------------|
| `--no-color` | Disable colored output |

**Examples:**

```bash
# Validate a YAML config
wrtkit validate config.yaml

# Validate a JSON config
wrtkit validate config.json
```

**Sample Output:**

```
Configuration is valid!
  - Network devices: 2
  - Network interfaces: 5
  - Wireless radios: 2
  - Wireless interfaces: 4
  - DHCP sections: 2
  - Firewall zones: 3
  - Firewall forwardings: 2
  - SQM queues: 0
  - Total UCI commands: 116
```

### `wrtkit commands`

Output all UCI commands from a configuration file as a shell script. Useful for manual deployment or inspection.

```bash
wrtkit commands CONFIG_FILE
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `CONFIG_FILE` | Path to a YAML or JSON configuration file |

**Examples:**

```bash
# Print commands to stdout
wrtkit commands config.yaml

# Save to a shell script
wrtkit commands config.yaml > deploy.sh

# Make executable and run manually on device
wrtkit commands config.yaml > deploy.sh
scp deploy.sh root@192.168.1.1:/tmp/
ssh root@192.168.1.1 "sh /tmp/deploy.sh"
```

### `wrtkit import`

Import the current configuration from a remote device and save it as a YAML or JSON file. This is useful for:

- Backing up router configurations
- Creating a baseline config from an existing router
- Cloning configurations to other devices

```bash
wrtkit import TARGET OUTPUT_FILE [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `TARGET` | Device to import from (IP, hostname, or serial port) |
| `OUTPUT_FILE` | Where to save the configuration (.yaml or .json) |

**Options:**

| Option | Description |
|--------|-------------|
| `-p, --password TEXT` | SSH/login password |
| `-k, --key-file PATH` | SSH private key file |
| `-t, --timeout INTEGER` | Connection timeout in seconds (default: 30) |
| `--format [yaml\|json]` | Output format (auto-detected from extension) |
| `--packages TEXT` | Comma-separated packages to import (default: all) |

**Examples:**

```bash
# Import full config from router
wrtkit import 192.168.1.1 router-backup.yaml

# Import as JSON
wrtkit import router.local config.json

# Import only network and wireless config
wrtkit import 192.168.1.1 minimal.yaml --packages network,wireless

# Import with password
wrtkit import 192.168.1.1 backup.yaml -p mypassword

# Clone config to another router
wrtkit import 192.168.1.1 template.yaml
wrtkit apply template.yaml 192.168.1.2
```

**Sample Output:**

```
Connecting to 192.168.1.1...
✓ Configuration imported

Configuration saved to router-backup.yaml
  - Network devices: 2
  - Network interfaces: 5
  - Wireless radios: 2
  - Wireless interfaces: 4
  - DHCP sections: 2
  - Firewall zones: 3
  - Firewall forwardings: 2
  - SQM queues: 0

You can now use this file with 'wrtkit apply router-backup.yaml <target>'
```

!!! tip "Cloning Routers"
    The `import` command is perfect for setting up multiple identical routers:

    1. Configure one router manually or with wrtkit
    2. Import its config: `wrtkit import 192.168.1.1 template.yaml`
    3. Apply to other routers: `wrtkit apply template.yaml 192.168.1.2`

## Target Formats

The `TARGET` argument supports multiple formats for specifying the device to connect to:

### SSH Connections

| Format | Example | Description |
|--------|---------|-------------|
| IP address | `192.168.1.1` | Connect via SSH to IP |
| Hostname | `router.local` | Connect via SSH to hostname |
| IP:port | `192.168.1.1:2222` | Connect via SSH on custom port |
| user@host | `root@192.168.1.1` | Connect with specific username |
| user@host:port | `admin@router.local:2222` | Full SSH connection string |

### Serial Connections

| Format | Example | Description |
|--------|---------|-------------|
| Linux serial | `/dev/ttyUSB0` | Serial port on Linux |
| macOS serial | `/dev/tty.usbserial` | Serial port on macOS |
| Windows serial | `COM3` | Serial port on Windows |

## Environment Variables

The CLI automatically loads environment variables from a `.env` file in the current directory. This is useful for storing credentials securely.

### Supported Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `WRTKIT_TARGET` | Default target device | `192.168.1.1` |
| `WRTKIT_PASSWORD` | SSH/login password | `mysecretpassword` |
| `WRTKIT_KEY_FILE` | Path to SSH private key | `/home/user/.ssh/id_rsa` |
| `WRTKIT_TIMEOUT` | Connection timeout in seconds | `60` |

Create a `.env` file in your project directory:

```bash
# .env
WRTKIT_TARGET=192.168.1.1
WRTKIT_PASSWORD=mysecretpassword
WRTKIT_KEY_FILE=/path/to/ssh/key
WRTKIT_TIMEOUT=60
```

Now you can run commands without specifying credentials:

```bash
# These will use values from .env
wrtkit preview config.yaml 192.168.1.1
wrtkit apply config.yaml 192.168.1.1

# Or even omit the target if WRTKIT_TARGET is set
wrtkit preview config.yaml
```

!!! tip "Security"
    Add `.env` to your `.gitignore` to avoid committing credentials to version control:
    ```bash
    echo ".env" >> .gitignore
    ```

## Configuration Files

The CLI works with both YAML and JSON configuration files. The format is automatically detected based on the file extension.

### YAML Example

```yaml
# config.yaml
network:
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
      channel: 6
      htmode: HT40
      country: US
  interfaces:
    wlan0:
      device: radio0
      mode: ap
      ssid: MyNetwork
      encryption: psk2
      key: MySecretKey
```

### JSON Example

```json
{
  "network": {
    "interfaces": {
      "lan": {
        "device": "br-lan",
        "proto": "static",
        "ipaddr": "192.168.1.1",
        "netmask": "255.255.255.0"
      }
    }
  }
}
```

For more details on configuration file format, see the [YAML/JSON Configuration Guide](../yaml-json-guide.md).

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (connection failed, invalid config, etc.) |

## Tips and Best Practices

### 1. Always Preview First

Before applying changes to a production device, always run `preview` or `apply --dry-run`:

```bash
wrtkit preview config.yaml 192.168.1.1 --show-commands
```

### 2. Use Version Control

Keep your configuration files in Git to track changes:

```bash
git init
echo ".env" >> .gitignore
git add config.yaml
git commit -m "Initial router configuration"
```

### 3. Test on Non-Production First

If possible, test your configuration on a spare device before deploying to production.

### 4. Use SSH Keys

For better security and automation, use SSH keys instead of passwords:

```bash
# Generate a key (if you don't have one)
ssh-keygen -t ed25519 -f ~/.ssh/wrtkit_key

# Copy to router
ssh-copy-id -i ~/.ssh/wrtkit_key root@192.168.1.1

# Use with CLI
wrtkit apply config.yaml 192.168.1.1 -k ~/.ssh/wrtkit_key
```

### 5. Scripting and Automation

The CLI is designed to work well in scripts:

```bash
#!/bin/bash
set -e

CONFIG="router-config.yaml"
DEVICES="192.168.1.1 192.168.1.2 192.168.1.3"

for device in $DEVICES; do
    echo "Deploying to $device..."
    wrtkit apply "$CONFIG" "$device" -k ~/.ssh/wrtkit_key -y
done

echo "Deployment complete!"
```

### 6. Use Fleet Mode for Multiple Devices

For managing multiple devices with coordinated updates, use [Fleet Mode](fleet.md):

```bash
# Apply to all devices in fleet with coordinated commit
wrtkit fleet apply fleet.yaml

# Target specific devices
wrtkit fleet apply fleet.yaml --target "ap-*"
wrtkit fleet apply fleet.yaml --tags production
```

Fleet mode ensures all devices commit their changes simultaneously, which is essential for network changes that might break connectivity.
