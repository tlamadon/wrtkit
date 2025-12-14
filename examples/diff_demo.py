#!/usr/bin/env python3
"""
Demo script showing the enhanced diff functionality.

This demonstrates:
1. Tracking remote-only UCI settings (settings on remote but not in local config)
2. Tree-structured diff report grouped by package and resource
"""

from wrtkit.base import UCICommand
from wrtkit.config import ConfigDiff


def demo_basic_diff():
    """Demonstrate basic diff with all types of changes."""
    print("=" * 60)
    print("BASIC DIFF OUTPUT (Linear Format)")
    print("=" * 60)

    diff = ConfigDiff()

    # Settings to add (in local config, not on remote)
    diff.to_add = [
        UCICommand("set", "network.lan.ipaddr", "192.168.1.1"),
        UCICommand("set", "network.lan.netmask", "255.255.255.0"),
        UCICommand("set", "wireless.radio0.channel", "11"),
    ]

    # Settings to modify (different values)
    diff.to_modify = [
        (
            UCICommand("set", "network.wan.proto", "static"),
            UCICommand("set", "network.wan.proto", "dhcp"),
        ),
        (
            UCICommand("set", "wireless.radio0.htmode", "HT40"),
            UCICommand("set", "wireless.radio0.htmode", "HT20"),
        ),
    ]

    # Remote-only settings (on remote but not managed by local config)
    diff.remote_only = [
        UCICommand("set", "network.guest.proto", "dhcp"),
        UCICommand("set", "network.guest.ipaddr", "192.168.2.1"),
        UCICommand("set", "wireless.radio1.channel", "36"),
        UCICommand("set", "firewall.@zone[2].name", "guest"),
    ]

    print(str(diff))
    print()


def demo_tree_diff():
    """Demonstrate tree-structured diff output."""
    print("=" * 60)
    print("TREE-STRUCTURED DIFF OUTPUT")
    print("=" * 60)

    diff = ConfigDiff()

    # Settings to add
    diff.to_add = [
        UCICommand("set", "network.lan.ipaddr", "192.168.1.1"),
        UCICommand("set", "network.lan.netmask", "255.255.255.0"),
        UCICommand("set", "network.lan.proto", "static"),
        UCICommand("set", "wireless.radio0.channel", "11"),
        UCICommand("set", "wireless.radio0.hwmode", "11g"),
        UCICommand("set", "dhcp.lan.start", "100"),
        UCICommand("set", "dhcp.lan.limit", "150"),
    ]

    # Settings to modify
    diff.to_modify = [
        (
            UCICommand("set", "network.wan.proto", "static"),
            UCICommand("set", "network.wan.proto", "dhcp"),
        ),
        (
            UCICommand("set", "wireless.radio0.htmode", "HT40"),
            UCICommand("set", "wireless.radio0.htmode", "HT20"),
        ),
        (
            UCICommand("set", "firewall.@zone[0].input", "DROP"),
            UCICommand("set", "firewall.@zone[0].input", "ACCEPT"),
        ),
    ]

    # Remote-only settings
    diff.remote_only = [
        UCICommand("set", "network.guest.proto", "dhcp"),
        UCICommand("set", "network.guest.ipaddr", "192.168.2.1"),
        UCICommand("set", "wireless.radio1.channel", "36"),
        UCICommand("set", "wireless.radio1.htmode", "VHT80"),
        UCICommand("set", "firewall.@zone[2].name", "guest"),
        UCICommand("set", "firewall.@zone[2].input", "REJECT"),
    ]

    print(diff.to_tree())
    print()


def demo_remote_only_feature():
    """Demonstrate the remote-only settings feature."""
    print("=" * 60)
    print("REMOTE-ONLY SETTINGS FEATURE")
    print("=" * 60)
    print("This shows UCI settings that exist on the remote device")
    print("but are not mentioned in the local configuration.")
    print()

    diff = ConfigDiff()

    # Only remote-only settings, no other changes
    diff.remote_only = [
        UCICommand("set", "system.@system[0].hostname", "openwrt"),
        UCICommand("set", "system.@system[0].timezone", "UTC"),
        UCICommand("set", "network.loopback.proto", "static"),
        UCICommand("set", "network.loopback.ipaddr", "127.0.0.1"),
        UCICommand("set", "wireless.default_radio0.encryption", "none"),
    ]

    print("Linear format:")
    print(str(diff))
    print()

    print("Tree format:")
    print(diff.to_tree())
    print()


def main():
    """Run all demos."""
    demo_basic_diff()
    demo_tree_diff()
    demo_remote_only_feature()

    print("=" * 60)
    print("KEY:")
    print("=" * 60)
    print("  \033[92m+\033[0m  = Settings to ADD (in local config, missing on remote) - GREEN")
    print("  \033[91m-\033[0m  = Settings to REMOVE (on remote, not in local config) - RED")
    print("  \033[93m~\033[0m  = Settings to MODIFY (different values) - YELLOW")
    print("  \033[96m*\033[0m  = REMOTE-ONLY settings (on remote, not managed by local) - CYAN")
    print()
    print("The tree format groups changes by:")
    print("  1. Package (network, wireless, dhcp, firewall)")
    print("  2. Section (lan, wan, radio0, etc.)")
    print("  3. Individual options within each section")
    print()
    print("Note: Colors are enabled by default. To disable:")
    print("  print(diff.to_string(color=False))")
    print("  print(diff.to_tree(color=False))")
    print()


if __name__ == "__main__":
    main()
