#!/usr/bin/env python3
"""
Debug script to test remote UCI config parsing.
This helps identify why remote settings might not be detected.
"""

from wrtkit.base import UCICommand
from wrtkit.config import UCIConfig


class MockSSH:
    """Mock SSH connection for testing the parser."""

    def __init__(self, mock_configs):
        """
        Args:
            mock_configs: Dict of package -> uci export output
        """
        self.mock_configs = mock_configs

    def get_uci_config(self, package: str) -> str:
        """Return mock UCI export output."""
        return self.mock_configs.get(package, "")


def test_parser():
    """Test the remote config parser with various UCI export formats."""

    # Simulate various UCI export formats
    mock_configs = {
        "network": """
# Network configuration
network.loopback=interface
network.loopback.device='lo'
network.loopback.proto='static'
network.loopback.ipaddr='127.0.0.1'
network.loopback.netmask='255.0.0.0'
network.lan=interface
network.lan.device='br-lan'
network.lan.proto='static'
network.lan.ipaddr='192.168.1.1'
network.lan.netmask='255.255.255.0'
network.guest=interface
network.guest.proto='dhcp'
network.guest.ipaddr='192.168.2.1'
""",
        "wireless": """
wireless.radio0=wifi-device
wireless.radio0.type='mac80211'
wireless.radio0.path='platform/soc/a000000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0'
wireless.radio0.channel='36'
wireless.radio0.htmode='VHT80'
wireless.radio0.country='US'
wireless.default_radio0=wifi-iface
wireless.default_radio0.device='radio0'
wireless.default_radio0.network='lan'
wireless.default_radio0.mode='ap'
wireless.default_radio0.ssid='OpenWrt'
wireless.default_radio0.encryption='none'
""",
        "dhcp": """
dhcp.lan=dhcp
dhcp.lan.interface='lan'
dhcp.lan.start='100'
dhcp.lan.limit='150'
dhcp.lan.leasetime='12h'
""",
        "firewall": """
firewall.@defaults[0]=defaults
firewall.@defaults[0].input='ACCEPT'
firewall.@defaults[0].output='ACCEPT'
firewall.@defaults[0].forward='REJECT'
firewall.@zone[0]=zone
firewall.@zone[0].name='lan'
firewall.@zone[0].input='ACCEPT'
firewall.@zone[0].output='ACCEPT'
firewall.@zone[0].forward='ACCEPT'
"""
    }

    # Create mock SSH and config
    mock_ssh = MockSSH(mock_configs)
    config = UCIConfig()

    # Parse remote config
    print("=" * 60)
    print("PARSING REMOTE CONFIG")
    print("=" * 60)

    remote_commands = config._parse_remote_config(mock_ssh)

    print(f"\nTotal commands parsed: {len(remote_commands)}\n")

    # Group by package
    by_package = {}
    for cmd in remote_commands:
        package = cmd.path.split(".")[0]
        if package not in by_package:
            by_package[package] = []
        by_package[package].append(cmd)

    for package in sorted(by_package.keys()):
        print(f"\n{package}/ ({len(by_package[package])} commands)")
        for cmd in by_package[package]:
            print(f"  {cmd.to_string()}")

    # Test specific patterns
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC PATTERNS")
    print("=" * 60)

    # Check if section definitions are parsed
    section_defs = [cmd for cmd in remote_commands if len(cmd.path.split(".")) == 2]
    print(f"\nSection definitions parsed: {len(section_defs)}")
    for cmd in section_defs[:5]:  # Show first 5
        print(f"  {cmd.to_string()}")

    # Check if options are parsed
    options = [cmd for cmd in remote_commands if len(cmd.path.split(".")) == 3]
    print(f"\nOptions parsed: {len(options)}")
    for cmd in options[:5]:  # Show first 5
        print(f"  {cmd.to_string()}")

    # Check if indexed sections are parsed
    indexed = [cmd for cmd in remote_commands if "@" in cmd.path]
    print(f"\nIndexed sections (firewall rules, etc.): {len(indexed)}")
    for cmd in indexed[:5]:
        print(f"  {cmd.to_string()}")

    # Test with empty local config
    print("\n" + "=" * 60)
    print("DIFF WITH EMPTY LOCAL CONFIG")
    print("=" * 60)
    print("(All remote settings should appear as remote-only)\n")

    diff = config.diff(mock_ssh, show_remote_only=True)

    print(f"Commands to add: {len(diff.to_add)}")
    print(f"Commands to modify: {len(diff.to_modify)}")
    print(f"Commands to remove: {len(diff.to_remove)}")
    print(f"Remote-only commands: {len(diff.remote_only)}")

    if diff.remote_only:
        print("\nRemote-only settings (showing first 10):")
        for cmd in diff.remote_only[:10]:
            print(f"  * {cmd.to_string()}")
    else:
        print("\n⚠️  WARNING: No remote-only settings detected!")
        print("This suggests the parser isn't working correctly.")

    # Show tree format
    print("\n" + "=" * 60)
    print("TREE FORMAT")
    print("=" * 60)
    print(diff.to_tree())


if __name__ == "__main__":
    test_parser()
