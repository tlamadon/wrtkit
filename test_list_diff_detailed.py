#!/usr/bin/env python3
"""
Detailed analysis of the list diff.
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


config = UCIConfig()
config.network.device("br_lan").name("br-lan").type("bridge").add_port("lan1").add_port("bat0.10")

ssh = MockSSH()
diff = config.diff(ssh, show_remote_only=True)

print("Common items:")
for cmd in diff.common:
    print(f"  {cmd.to_string()}")
