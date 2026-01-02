# Fleet Mode

Fleet mode enables managing multiple OpenWRT devices from a single inventory file with **coordinated atomic updates**. This is essential for network changes that might break connectivity - all devices commit their changes simultaneously.

## Overview

When you change network settings on a router or access point, the device often needs to restart network services. If you're managing multiple devices and they have interdependent configurations (like mesh networks or VLANs), updating them one at a time can break connectivity.

Fleet mode solves this with **two-phase execution**:

1. **Stage Phase**: Push all configuration changes to all devices in parallel (without committing)
2. **Commit Phase**: All devices commit and restart services at the same time

If any device fails during staging, all changes are rolled back before anything is committed.

## Quick Start

### 1. Create a Fleet Inventory File

```yaml
# fleet.yaml
defaults:
  timeout: 30
  username: root
  commit_delay: 10  # seconds before synchronized commit

config_layers:
  base: configs/base-router.yaml

devices:
  main-router:
    target: 192.168.1.1
    password: ${oc.env:ROUTER_PASSWORD}
    configs:
      - ${config_layers.base}
      - configs/main-router.yaml
    tags: [core, production]

  ap-living-room:
    target: 192.168.1.10
    key_file: ~/.ssh/openwrt_key
    configs:
      - ${config_layers.base}
      - configs/ap-config.yaml
    tags: [ap, production]
```

### 2. Validate Your Fleet File

```bash
wrtkit fleet validate fleet.yaml
```

### 3. Preview Changes

```bash
wrtkit fleet preview fleet.yaml
```

### 4. Apply Changes

```bash
wrtkit fleet apply fleet.yaml
```

## CLI Commands

### `wrtkit fleet apply`

Apply configuration to fleet devices with coordinated updates.

```bash
# Apply to all devices
wrtkit fleet apply fleet.yaml

# Apply to specific device
wrtkit fleet apply fleet.yaml --target main-router

# Apply to devices matching glob pattern
wrtkit fleet apply fleet.yaml --target "ap-*"

# Apply to devices with specific tags
wrtkit fleet apply fleet.yaml --tags production

# Multiple tags (AND logic)
wrtkit fleet apply fleet.yaml --tags "ap,production"

# Dry run (preview only)
wrtkit fleet apply fleet.yaml --dry-run

# Skip confirmation prompt
wrtkit fleet apply fleet.yaml -y

# Custom commit delay
wrtkit fleet apply fleet.yaml --commit-delay 30
```

**Options:**

| Option | Description |
|--------|-------------|
| `--target, -t` | Device name or glob pattern (e.g., `ap-*`) |
| `--tags` | Comma-separated tags to filter by (AND logic) |
| `--commit-delay` | Seconds to wait before coordinated commit |
| `--remove-unmanaged` | Remove settings not in config |
| `--dry-run` | Show what would be done without applying |
| `-y, --yes` | Skip confirmation prompt |
| `--no-color` | Disable colored output |

### `wrtkit fleet preview`

Preview configuration changes for fleet devices without applying.

```bash
wrtkit fleet preview fleet.yaml
wrtkit fleet preview fleet.yaml --target main-router
wrtkit fleet preview fleet.yaml --tags production
```

### `wrtkit fleet validate`

Validate fleet file and all referenced configurations.

```bash
wrtkit fleet validate fleet.yaml
```

This checks:

- Fleet file syntax and schema
- All referenced config files exist
- Config files are valid YAML

### `wrtkit fleet show`

Show the merged configuration for a specific device.

```bash
wrtkit fleet show fleet.yaml --target main-router
wrtkit fleet show fleet.yaml --target main-router --format json
```

## Fleet Inventory Schema

### `defaults`

Default settings applied to all devices:

```yaml
defaults:
  timeout: 30          # Connection timeout in seconds
  username: root       # Default SSH username
  commit_delay: 10     # Seconds before synchronized commit/reload
```

### `config_layers`

Named configuration files that can be referenced by devices:

```yaml
config_layers:
  base: configs/base-router.yaml
  security: configs/security-hardening.yaml
  ap_config: configs/wireless-ap.yaml
```

These can be referenced in device configs using OmegaConf interpolation: `${config_layers.base}`

### `devices`

Dictionary of device definitions:

```yaml
devices:
  device-name:
    target: 192.168.1.1           # Required: IP, hostname, or serial port
    username: root                 # Optional: override default username
    password: secret               # Optional: SSH password
    key_file: ~/.ssh/key          # Optional: SSH private key
    timeout: 60                    # Optional: override default timeout
    configs:                       # List of config files to merge
      - ${config_layers.base}
      - configs/device-specific.yaml
    tags:                          # Tags for filtering
      - production
      - core
```

## Device Targeting

### By Name

Target a specific device by its exact name:

```bash
wrtkit fleet apply fleet.yaml --target main-router
```

### By Glob Pattern

Target multiple devices using glob patterns:

```bash
# All devices starting with "ap-"
wrtkit fleet apply fleet.yaml --target "ap-*"

# All devices ending with "-production"
wrtkit fleet apply fleet.yaml --target "*-production"
```

### By Tags

Target devices by tags (AND logic - device must have all specified tags):

```bash
# All devices with "production" tag
wrtkit fleet apply fleet.yaml --tags production

# Devices with both "ap" AND "production" tags
wrtkit fleet apply fleet.yaml --tags "ap,production"
```

## Configuration Merging

When a device has multiple config files, they are merged using OmegaConf in order. Later files override earlier ones:

```yaml
devices:
  main-router:
    configs:
      - configs/base.yaml        # Base settings
      - configs/security.yaml    # Security overrides
      - configs/router.yaml      # Device-specific settings
```

This allows you to build layered configurations:

- **Base layer**: Common settings for all devices
- **Role layer**: Settings for specific device roles (router, AP, etc.)
- **Device layer**: Device-specific overrides

## Variable Interpolation

Fleet files support OmegaConf variable interpolation:

### Environment Variables

```yaml
devices:
  main-router:
    password: ${oc.env:ROUTER_PASSWORD}
    # With default value
    password: ${oc.env:ROUTER_PASSWORD,default_password}
```

### Config Layer References

```yaml
config_layers:
  base: configs/base.yaml

devices:
  main-router:
    configs:
      - ${config_layers.base}  # References the base config layer
```

## Two-Phase Execution

### Phase 1: Staging

During the staging phase:

1. Connect to all targeted devices in parallel
2. Merge configuration files for each device
3. Compute diff between current and desired state
4. Execute UCI commands (set, add_list, delete) **without committing**
5. If **any device fails**, abort and rollback all staged changes

### Phase 2: Coordinated Commit

Once all devices are successfully staged:

1. Send background commit commands to all devices:
   ```bash
   nohup sh -c 'sleep $DELAY && uci commit && /etc/init.d/network restart && wifi reload' &
   ```
2. All devices wait for the same delay, then commit simultaneously
3. Network services restart at approximately the same time

### Why Two-Phase?

Consider a mesh network with multiple nodes. If you update the mesh encryption key on one node at a time, that node loses connectivity to the mesh until all nodes have the new key.

With two-phase execution:

1. All nodes stage the new key (but don't apply it)
2. All nodes commit at the same time
3. Brief network interruption as all nodes restart
4. All nodes come back up with the new configuration

## Example Output

```
$ wrtkit fleet apply fleet.yaml --tags production

Fleet: fleet.yaml
Targets: 3 device(s) (filtered by tags: production)

This will apply changes to 3 device(s).
Continue? [y/N]: y

[Phase 1: Staging Changes]
  main-router (192.168.1.1)... OK - 12 changes
  ap-living-room (192.168.1.10)... OK - 8 changes
  ap-office (192.168.1.11)... OK - 8 changes

[Phase 2: Coordinated Commit (delay: 10s)]
  main-router (192.168.1.1)... OK - 0 changes
  ap-living-room (192.168.1.10)... OK - 0 changes
  ap-office (192.168.1.11)... OK - 0 changes

Fleet apply completed: 3/3 devices updated
```

## Error Handling

### Staging Failure

If any device fails during staging, all changes are rolled back:

```
[Phase 1: Staging Changes]
  main-router (192.168.1.1)... OK - 12 changes
  ap-living-room (192.168.1.10)... FAILED - Connection refused

Fleet apply ABORTED: Device 'ap-living-room' failed: Connection refused
All staged changes have been rolled back.
```

### Partial Commit

If commit fails on some devices (rare, since staging succeeded):

```
Fleet apply partial: 2/3 devices updated
  - ap-office: Connection timeout during commit
```

## Best Practices

### 1. Always Validate First

```bash
wrtkit fleet validate fleet.yaml
```

### 2. Preview Before Applying

```bash
wrtkit fleet preview fleet.yaml
```

### 3. Use Tags for Gradual Rollout

```yaml
devices:
  ap-test:
    tags: [ap, testing]
  ap-prod-1:
    tags: [ap, production]
  ap-prod-2:
    tags: [ap, production]
```

```bash
# Test on staging devices first
wrtkit fleet apply fleet.yaml --tags testing

# Then roll out to production
wrtkit fleet apply fleet.yaml --tags production
```

### 4. Keep Commit Delay Reasonable

The default 10-second delay works well for most scenarios. Increase it for:

- Large fleets where command dispatch takes time
- Slow network connections
- Complex configurations that take longer to parse

### 5. Use Environment Variables for Secrets

```yaml
devices:
  main-router:
    password: ${oc.env:ROUTER_PASSWORD}
```

```bash
export ROUTER_PASSWORD="secure_password"
wrtkit fleet apply fleet.yaml
```

## Example Fleet File

See [examples/fleet.yaml](https://github.com/tlamadon/wrtkit/blob/main/examples/fleet.yaml) for a complete example.

```yaml
# Complete fleet.yaml example
defaults:
  timeout: 30
  username: root
  commit_delay: 10

config_layers:
  base: base-router-config.yaml
  wireless_ap: wireless-ap.yaml

devices:
  main-router:
    target: 192.168.1.1
    password: ${oc.env:ROUTER_PASSWORD,default_password}
    configs:
      - ${config_layers.base}
      - router-config.yaml
    tags:
      - core
      - production

  ap-living-room:
    target: 192.168.1.10
    key_file: ~/.ssh/openwrt_key
    configs:
      - ${config_layers.base}
      - ${config_layers.wireless_ap}
    tags:
      - ap
      - production

  ap-office:
    target: 192.168.1.11
    password: ${oc.env:AP_PASSWORD,default_password}
    timeout: 60
    configs:
      - ${config_layers.base}
      - ${config_layers.wireless_ap}
    tags:
      - ap
      - production

  dev-router:
    target: 192.168.100.1:2222
    password: ${oc.env:DEV_PASSWORD,devpassword}
    configs:
      - ${config_layers.base}
      - test-config.yaml
    tags:
      - development
      - testing
```
