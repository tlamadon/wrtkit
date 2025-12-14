#!/usr/bin/env python3
"""
Demo script showing colored diff output.
"""

from wrtkit.base import UCICommand
from wrtkit.config import ConfigDiff


def main():
    print("=" * 60)
    print("COLORED DIFF OUTPUT DEMO")
    print("=" * 60)

    diff = ConfigDiff()

    # Add some changes
    diff.to_add = [
        UCICommand("set", "network.lan.ipaddr", "192.168.1.1"),
        UCICommand("set", "network.lan.netmask", "255.255.255.0"),
        UCICommand("set", "network.lan.proto", "static"),
        UCICommand("set", "wireless.radio0.channel", "11"),
    ]

    # Modifications
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

    # Remote-only settings
    diff.remote_only = [
        UCICommand("set", "network.guest.proto", "dhcp"),
        UCICommand("set", "network.guest.ipaddr", "192.168.2.1"),
        UCICommand("set", "wireless.radio1.channel", "36"),
        UCICommand("set", "wireless.radio1.htmode", "VHT80"),
        UCICommand("set", "firewall.@zone[2].name", "guest"),
    ]

    # Common settings (matching between local and remote)
    diff.common = [
        UCICommand("set", "network.loopback.proto", "static"),
        UCICommand("set", "network.loopback.device", "lo"),
        UCICommand("set", "system.@system[0].hostname", "OpenWrt"),
    ]

    print("\n" + "=" * 60)
    print("LINEAR FORMAT (with colors)")
    print("=" * 60)
    print(str(diff))  # Uses color by default

    print("\n" + "=" * 60)
    print("TREE FORMAT (with colors)")
    print("=" * 60)
    print(diff.to_tree())  # Uses color by default

    print("\n" + "=" * 60)
    print("COLOR LEGEND")
    print("=" * 60)
    print(f"  \033[92m+\033[0m  GREEN   = Commands to ADD (in local config, missing on remote)")
    print(f"  \033[91m-\033[0m  RED     = Commands to REMOVE (on remote, not in local)")
    print(f"  \033[93m~\033[0m  YELLOW  = Commands to MODIFY (different values)")
    print(f"  \033[96m*\033[0m  CYAN    = REMOTE-ONLY (on remote, not managed by local)")
    print()

    # Show without colors for comparison
    print("\n" + "=" * 60)
    print("WITHOUT COLORS (for comparison)")
    print("=" * 60)
    print(diff.to_string(color=False))


if __name__ == "__main__":
    main()
