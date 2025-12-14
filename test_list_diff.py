#!/usr/bin/env python3
"""
Test to demonstrate the list item diff issue.
"""

from wrtkit.base import UCICommand
from wrtkit.config import UCIConfig


class MockSSH:
    """Mock SSH with list items."""
    
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


def main():
    print("=" * 60)
    print("LIST ITEM DIFF TEST")
    print("=" * 60)
    
    # Create local config with different list items
    config = UCIConfig()
    config.network.device("br_lan").name("br-lan").type("bridge").add_port("lan1").add_port("bat0.10")
    
    # Get diff
    ssh = MockSSH()
    diff = config.diff(ssh, show_remote_only=True)
    
    print("\nLocal commands:")
    for cmd in config.get_all_commands():
        if "ports" in cmd.path:
            print(f"  {cmd.to_string()}")
    
    print("\nRemote commands (parsed):")
    remote_cmds = config._parse_remote_config(ssh)
    for cmd in remote_cmds:
        if "ports" in cmd.path:
            print(f"  {cmd.to_string()}")
    
    print("\n" + "=" * 60)
    print("DIFF RESULT")
    print("=" * 60)
    print(diff.to_string(color=False))
    
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    print(f"Commands to add: {len(diff.to_add)}")
    print(f"Commands to modify: {len(diff.to_modify)}")
    print(f"Remote-only: {len(diff.remote_only)}")
    print(f"Common: {len(diff.common)}")
    
    print("\nExpected behavior:")
    print("  - 'lan1' should be in common (exists in both)")
    print("  - 'bat0.10' should be to add (local only)")
    print("  - 'lan2' and 'lan3' should be remote-only (remote only)")


if __name__ == "__main__":
    main()
