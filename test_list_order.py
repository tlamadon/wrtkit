#!/usr/bin/env python3
"""
Test list items in different order - bat0.10 at the end.
"""

from wrtkit.config import UCIConfig


class MockSSH:
    def get_uci_config(self, package: str) -> str:
        if package == "network":
            return """config device 'br_lan'
	option name 'br-lan'
	option type 'bridge'
	list ports 'lan1'
	list ports 'lan2'
	list ports 'lan3'
"""
        return ""


print("=" * 70)
print("TEST: bat0.10 at the END of local config")
print("=" * 70)

config = UCIConfig()
# Add ports in same order as remote, plus bat0.10 at the end
config.network.device("br_lan").name("br-lan").type("bridge") \
    .add_port("lan1").add_port("lan2").add_port("lan3").add_port("bat0.10")

ssh = MockSSH()
diff = config.diff(ssh, show_remote_only=True)

print("\nLocal commands (in order):")
for cmd in config.get_all_commands():
    if "ports" in cmd.path:
        print(f"  {cmd.to_string()}")

print("\nRemote commands (parsed):")
remote_cmds = config._parse_remote_config(ssh)
for cmd in remote_cmds:
    if "ports" in cmd.path:
        print(f"  {cmd.to_string()}")

print("\n" + "=" * 70)
print("DIFF OUTPUT")
print("=" * 70)
print(diff.to_string(color=False))

print("\n" + "=" * 70)
print("EXPECTED vs ACTUAL")
print("=" * 70)
print("Expected:")
print("  - lan1, lan2, lan3 should be COMMON")
print("  - bat0.10 should be TO ADD")
print()
print("Actual:")
to_add_ports = [cmd for cmd in diff.to_add if "ports" in cmd.path]
common_ports = [cmd for cmd in diff.common if "ports" in cmd.path]
remote_only_ports = [cmd for cmd in diff.remote_only if "ports" in cmd.path]

print(f"  - Common ports: {[cmd.value for cmd in common_ports]}")
print(f"  - To add ports: {[cmd.value for cmd in to_add_ports]}")
print(f"  - Remote-only ports: {[cmd.value for cmd in remote_only_ports]}")
