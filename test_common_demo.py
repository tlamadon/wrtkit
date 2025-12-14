#!/usr/bin/env python3
"""
Demo showing the common settings count feature.
"""

from wrtkit.base import UCICommand
from wrtkit.config import ConfigDiff


def main():
    print("=" * 60)
    print("COMMON SETTINGS TRACKING DEMO")
    print("=" * 60)
    
    diff = ConfigDiff()
    
    # Settings that will be added (in local config but not remote)
    diff.to_add = [
        UCICommand("set", "network.guest.ipaddr", "192.168.2.1"),
        UCICommand("set", "network.guest.netmask", "255.255.255.0"),
    ]
    
    # Settings that will be modified (different values)
    diff.to_modify = [
        (
            UCICommand("set", "network.wan.proto", "static"),
            UCICommand("set", "network.wan.proto", "dhcp"),
        ),
    ]
    
    # Settings on remote only (not managed by local config)
    diff.remote_only = [
        UCICommand("set", "network.vpn.proto", "wireguard"),
        UCICommand("set", "firewall.@zone[2].name", "vpn"),
    ]
    
    # Settings that match between local and remote (NEW!)
    diff.common = [
        UCICommand("set", "network.lan", "interface"),
        UCICommand("set", "network.lan.ipaddr", "192.168.1.1"),
        UCICommand("set", "network.lan.netmask", "255.255.255.0"),
        UCICommand("set", "network.lan.proto", "static"),
        UCICommand("set", "system.@system[0].hostname", "OpenWrt"),
        UCICommand("set", "system.@system[0].timezone", "UTC"),
    ]
    
    print("\n" + "=" * 60)
    print("DIFF OUTPUT")
    print("=" * 60)
    print(str(diff))
    
    print("\n" + "=" * 60)
    print("INTERPRETATION")
    print("=" * 60)
    print(f"✓ {len(diff.common)} settings are already configured correctly")
    print(f"+ {len(diff.to_add)} new settings will be added")
    print(f"~ {len(diff.to_modify)} settings will be modified")
    print(f"* {len(diff.remote_only)} settings exist but aren't managed by your config")
    print()
    print("This helps you understand what portion of your configuration")
    print("is already in sync with the remote device!")


if __name__ == "__main__":
    main()
