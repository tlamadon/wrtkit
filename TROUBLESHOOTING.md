# Troubleshooting Remote Config Detection

If the diff engine isn't detecting remote-only UCI settings, use this guide to diagnose the issue.

## Quick Diagnostic

Run the debug script:

```bash
python debug_remote_parsing.py  # Test with mock data
python test_real_ssh.py          # Test with real device
```

## Common Issues

### 1. SSH Connection Fails

**Symptom:** Error connecting to device or retrieving UCI config

**Solutions:**
- Verify device IP is correct
- Check SSH is enabled on OpenWRT (`/etc/init.d/dropbear status`)
- Ensure firewall allows SSH connections
- Test SSH manually: `ssh root@192.168.1.1 "uci export network"`

### 2. Empty Config Returned

**Symptom:** `Remote-only commands: 0` when device clearly has config

**Possible causes:**

a) **Package doesn't exist on device**
   ```python
   # Check what packages are available
   ssh.execute("opkg list-installed | grep uci")
   ```

b) **UCI export fails silently**
   ```python
   # Test manually
   stdout, stderr, code = ssh.execute("uci export network")
   print(f"Exit code: {code}")
   print(f"Output: {stdout}")
   print(f"Errors: {stderr}")
   ```

c) **Parser errors are hidden**

   The parser catches all exceptions. Check for warnings:
   ```
   Warning: Could not retrieve network config: ...
   ```

### 3. Parser Not Handling UCI Format

**Symptom:** Some settings detected, others missing

The parser at [config.py:221-258](src/wrtkit/config.py:221-258) only handles:
- Section definitions: `package.section=type`
- Options: `package.section.option=value`

**Not currently handled:**
- UCI lists with multiple values
- List items: `package.section.option='value1' 'value2'`
- Some complex array syntax

**Workaround:** The parser will skip unsupported lines but process others.

### 4. Comparison Logic Issues

**Symptom:** Settings exist in `diff.to_add` or `diff.to_modify` instead of `diff.remote_only`

This happens when:
- Same path exists in local config with different value → `to_modify`
- Local config mentions the path → not considered remote-only

**Example:**
```python
# Local config has:
config.network.interface("lan").proto("static")

# Remote has:
network.lan.proto='dhcp'

# Result: Goes to diff.to_modify, NOT diff.remote_only
```

### 5. show_remote_only=False

**Symptom:** Settings appear in `diff.to_remove` instead of `diff.remote_only`

**Solution:** Ensure you're using `show_remote_only=True` (default):

```python
diff = config.diff(ssh, show_remote_only=True)
```

## Debugging Steps

### Step 1: Test SSH Connection

```python
from wrtkit import SSHConnection

ssh = SSHConnection(host="192.168.1.1", username="root", password="your-password")

# Test basic command
stdout, stderr, code = ssh.execute("uname -a")
print(f"Device: {stdout}")

# Test UCI export
for pkg in ["network", "wireless", "dhcp", "firewall"]:
    stdout, stderr, code = ssh.execute(f"uci export {pkg}")
    print(f"\n{pkg}: {len(stdout)} bytes, exit code {code}")
    if stderr:
        print(f"  Errors: {stderr}")
```

### Step 2: Test Parser

```python
from wrtkit import UCIConfig

config = UCIConfig()

# Use your real SSH connection
remote_commands = config._parse_remote_config(ssh)

print(f"Parsed {len(remote_commands)} commands")

# Group by package
by_pkg = {}
for cmd in remote_commands:
    pkg = cmd.path.split(".")[0]
    by_pkg[pkg] = by_pkg.get(pkg, 0) + 1

for pkg, count in sorted(by_pkg.items()):
    print(f"  {pkg}: {count} commands")
```

### Step 3: Test Diff Logic

```python
# Empty local config - everything should be remote-only
config = UCIConfig()
diff = config.diff(ssh, show_remote_only=True)

print(f"Add: {len(diff.to_add)}")
print(f"Modify: {len(diff.to_modify)}")
print(f"Remove: {len(diff.to_remove)}")
print(f"Remote-only: {len(diff.remote_only)}")

# If remote_only is 0, something is wrong with parser or SSH
# If remote_only > 0, parser is working!
```

### Step 4: Check Actual Output

```python
# See what the remote device actually returns
ssh = SSHConnection(host="192.168.1.1", username="root", password="password")
output, _, _ = ssh.execute("uci export network")

print("Raw UCI export output:")
print(output)

# Check format
lines = output.strip().split("\n")
print(f"\nTotal lines: {len(lines)}")
print("Sample lines:")
for line in lines[:10]:
    print(f"  '{line}'")
```

## Known Limitations

1. **Section type definitions** (`network.lan=interface`) are included in remote_only
   - This is by design - they're part of the configuration

2. **Indexed sections** (`firewall.@zone[0]=zone`) are supported
   - Parser handles `@` syntax correctly

3. **List options** with multiple values may not parse correctly
   - Example: `network.br_lan.ports='lan1 lan2 lan3'` might fail

4. **Anonymous sections** (firewall rules) work
   - Example: `firewall.@rule[0].src='wan'`

## Getting Help

If you're still having issues:

1. Run `python debug_remote_parsing.py` - Does it work with mock data?
2. Run `python test_real_ssh.py` - Does it work with your device?
3. Check for warning messages during diff
4. Verify SSH access: `ssh root@192.168.1.1 "uci export network"`
5. Check UCI is installed: `ssh root@192.168.1.1 "which uci"`

## Example Working Configuration

```python
from wrtkit import UCIConfig, SSHConnection

# Connect to device
ssh = SSHConnection(
    host="192.168.1.1",
    username="root",
    password="your-password",
    timeout=30  # Increase if device is slow
)

# Create empty config
config = UCIConfig()

# Get diff - should show all remote settings as remote-only
diff = config.diff(ssh, show_remote_only=True)

if diff.remote_only:
    print(f"✓ Found {len(diff.remote_only)} remote-only settings")
    print(diff.to_tree())
else:
    print("✗ No remote settings detected - see troubleshooting guide")

ssh.close()
```
