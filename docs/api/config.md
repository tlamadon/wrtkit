# UCIConfig API

Main configuration class for managing UCI configuration.

## Overview

The `UCIConfig` class is the main entry point for creating OpenWRT configurations. It aggregates all configuration managers (network, wireless, DHCP, firewall).

## Class Reference

::: wrtkit.config.UCIConfig
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - get_all_commands
        - to_script
        - save_to_file
        - diff
        - apply

## ConfigDiff Class

::: wrtkit.config.ConfigDiff
    options:
      show_root_heading: true
      show_source: true

## Usage Example

```python
from wrtkit import UCIConfig

config = UCIConfig()

# Access configuration managers
config.network    # NetworkConfig instance
config.wireless   # WirelessConfig instance
config.dhcp       # DHCPConfig instance
config.firewall   # FirewallConfig instance

# Generate script
script = config.to_script()

# Save to file
config.save_to_file("config.sh")

# Get all commands
commands = config.get_all_commands()
```

## See Also

- [Network API](network.md)
- [Wireless API](wireless.md)
- [DHCP API](dhcp.md)
- [Firewall API](firewall.md)
