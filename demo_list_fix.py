#!/usr/bin/env python3
"""
Demo showing the list item diff fix.
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
print("UCI LIST ITEMS DIFF - DEMONSTRATION")
print("=" * 70)

config = UCIConfig()
config.network.device("br_lan").name("br-lan").type("bridge").add_port("lan1").add_port("bat0.10")

ssh = MockSSH()
diff = config.diff(ssh, show_remote_only=True)

print("\n📋 SCENARIO:")
print("  Local config:  br-lan bridge with ports ['lan1', 'bat0.10']")
print("  Remote config: br-lan bridge with ports ['lan1', 'lan2', 'lan3']")

print("\n" + "=" * 70)
print("DIFF OUTPUT (Tree Format)")
print("=" * 70)
print(diff.to_tree())

print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)
print("✓ The diff correctly identifies:")
print("  • 'lan1' port exists in BOTH → counted as common")
print("  • 'bat0.10' port only in local → will be ADDED to remote")
print("  • 'lan2' and 'lan3' ports only on remote → marked as remote-only")
print()
print("This means if you apply this config:")
print("  1. 'bat0.10' will be added to the bridge")
print("  2. 'lan2' and 'lan3' will remain (not removed, just unmanaged)")
print("  3. 'lan1' stays as-is (already correct)")
