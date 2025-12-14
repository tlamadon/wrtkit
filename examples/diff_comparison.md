# Diff Output Comparison

This document shows the difference between the enhanced diff formats.

## Scenario

You have a local configuration that defines:
- `network.lan.ipaddr = 192.168.1.1`
- `network.lan.netmask = 255.255.255.0`
- `network.wan.proto = dhcp` (remote has `static`)
- `wireless.radio0.channel = 11`
- `wireless.radio0.htmode = HT20` (remote has `HT40`)

The remote device also has settings you're not managing:
- `network.guest.proto = dhcp`
- `network.guest.ipaddr = 192.168.2.1`
- `wireless.radio1.channel = 36`
- `firewall.@zone[2].name = guest`

## Linear Format Output

```python
diff = config.diff(ssh)
print(str(diff))
```

**Output:**
```
Commands to add:
  + uci set network.lan.ipaddr='192.168.1.1'
  + uci set network.lan.netmask='255.255.255.0'
  + uci set wireless.radio0.channel='11'

Commands to modify:
  - uci set network.wan.proto='static'
  + uci set network.wan.proto='dhcp'
  - uci set wireless.radio0.htmode='HT40'
  + uci set wireless.radio0.htmode='HT20'

Remote-only settings (not managed by config):
  * uci set network.guest.proto='dhcp'
  * uci set network.guest.ipaddr='192.168.2.1'
  * uci set wireless.radio1.channel='36'
  * uci set firewall.@zone[2].name='guest'
```

## Tree Format Output

```python
diff = config.diff(ssh)
print(diff.to_tree())
```

**Output:**
```
firewall/
└── @zone[2]
      * name = guest (remote-only)

network/
├── guest
│     * proto = dhcp (remote-only)
│     * ipaddr = 192.168.2.1 (remote-only)
├── lan
│     + ipaddr = 192.168.1.1
│     + netmask = 255.255.255.0
└── wan
      ~ proto
        - static
        + dhcp

wireless/
├── radio0
│     + channel = 11
│     ~ htmode
│       - HT40
│       + HT20
└── radio1
      * channel = 36 (remote-only)
```

## Benefits of Tree Format

### 1. **Hierarchical Organization**
Changes are grouped by package (network, wireless, firewall) and then by section (lan, wan, radio0), making it easy to see which resources are affected.

### 2. **Visual Structure**
The tree structure with `├──`, `└──`, and `│` characters clearly shows the relationship between packages, sections, and options.

### 3. **Grouped Context**
All changes to a specific resource (e.g., `network.lan`) are shown together, rather than scattered across different sections.

### 4. **Clear Remote-Only Identification**
Remote-only settings are visually distinct with the `*` symbol and `(remote-only)` label, making it easy to identify unmanaged configuration.

### 5. **Easier to Scan**
For large configurations, the tree format is easier to scan and understand at a glance.

## When to Use Each Format

### Use Linear Format When:
- You want to see the exact UCI commands
- You're scripting or parsing the output
- You prefer a simple, flat list
- You're familiar with standard diff output

### Use Tree Format When:
- You have many changes across multiple packages
- You want to understand changes by resource grouping
- You're reviewing configuration before applying
- You need to identify which packages/sections are affected
- You want a clearer view of remote-only settings

## Code Examples

### Get both formats:
```python
from wrtkit import UCIConfig, SSHConnection

config = UCIConfig()
# ... configure settings ...

ssh = SSHConnection(host="192.168.1.1", username="root", password="secret")
diff = config.diff(ssh)

# Show linear format
print("=== LINEAR FORMAT ===")
print(str(diff))
print()

# Show tree format
print("=== TREE FORMAT ===")
print(diff.to_tree())
```

### Save to files:
```python
# Save both formats for review
with open("diff_linear.txt", "w") as f:
    f.write(str(diff))

with open("diff_tree.txt", "w") as f:
    f.write(diff.to_tree())
```

### Conditionally show remote-only:
```python
# Track remote-only settings (default)
diff = config.diff(ssh, show_remote_only=True)
if diff.remote_only:
    print("Found unmanaged remote settings:")
    print(diff.to_tree())

# Or treat them as settings to remove (old behavior)
diff = config.diff(ssh, show_remote_only=False)
if diff.to_remove:
    print("Settings to remove:")
    print(diff.to_tree())
```
