#!/usr/bin/env python3
"""
Test the exact scenario you described: ['lan1', 'lan2', 'lan3', 'bat0.10']
"""

from wrtkit.config import UCIConfig


class MockSSH:
    def get_uci_config(self, package: str) -> str:
        if package == "network":
            # Remote has lan1, lan2, lan3
            return """config device 'br_lan'
	option name 'br-lan'
	option type 'bridge'
	list ports 'lan1'
	list ports 'lan2'
	list ports 'lan3'
"""
        return ""


print("=" * 70)
print("YOUR SCENARIO TEST")
print("=" * 70)
print("Remote device has: ['lan1', 'lan2', 'lan3']")
print("Local config has:  ['lan1', 'lan2', 'lan3', 'bat0.10']")
print()

config = UCIConfig()

# Build the exact list you mentioned: lan1, lan2, lan3, bat0.10
builder = config.network.device("br_lan").name("br-lan").type("bridge")
for port in ['lan1', 'lan2', 'lan3', 'bat0.10']:
    builder = builder.add_port(port)

ssh = MockSSH()
diff = config.diff(ssh, show_remote_only=True)

print("=" * 70)
print("LINEAR DIFF OUTPUT")
print("=" * 70)
print(diff.to_string(color=False))

print("\n" + "=" * 70)
print("TREE DIFF OUTPUT")
print("=" * 70)
print(diff.to_tree(color=False))

print("\n" + "=" * 70)
print("DETAILED ANALYSIS")
print("=" * 70)

# Check each port individually
local_ports = [cmd.value for cmd in config.get_all_commands() if "ports" in cmd.path]
remote_ports = [cmd.value for cmd in config._parse_remote_config(ssh) if "ports" in cmd.path]

print(f"Local ports:  {local_ports}")
print(f"Remote ports: {remote_ports}")
print()

to_add_ports = [cmd.value for cmd in diff.to_add if "ports" in cmd.path]
common_ports = [cmd.value for cmd in diff.common if "ports" in cmd.path]
remote_only_ports = [cmd.value for cmd in diff.remote_only if "ports" in cmd.path]

print(f"✓ Common (exist in both):     {common_ports}")
print(f"+ To add (local only):        {to_add_ports}")
print(f"* Remote-only (remote only):  {remote_only_ports}")

if 'bat0.10' in to_add_ports:
    print("\n✅ SUCCESS: bat0.10 is correctly detected as 'to add'")
else:
    print("\n❌ FAILURE: bat0.10 is NOT detected as 'to add'")
    print(f"   Instead, bat0.10 is in: ", end="")
    if 'bat0.10' in common_ports:
        print("COMMON")
    elif 'bat0.10' in remote_only_ports:
        print("REMOTE-ONLY")
    else:
        print("NOWHERE (this is a bug!)")
