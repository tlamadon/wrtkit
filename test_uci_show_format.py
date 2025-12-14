#!/usr/bin/env python3
"""
Test the parser with the actual 'uci show' format output.
"""

from wrtkit import UCIConfig


class MockSSH:
    """Mock SSH with real uci show output."""

    def get_uci_config(self, package: str) -> str:
        """Return real UCI show format output."""
        if package == "network":
            return """package network

config interface 'loopback'
	option device 'lo'
	option proto 'static'
	list ipaddr '127.0.0.1/8'

config globals 'globals'
	option dhcp_default_duid '00049a963f170a074dee81c6fb1e24235be0'
	option ula_prefix 'fd1c:7316:9e66::/48'

config interface 'lan'
	option device 'br-lan'
	option proto 'static'
	option ipaddr '192.168.10.1'
	option netmask '255.255.255.0'
	option ipv6 '0'

config interface 'wan'
	option device 'eth1'
	option proto 'dhcp'
	option ipv6 '0'

config interface 'wan6'
	option device 'eth1'
	option proto 'dhcpv6'
	option disabled '1'

config interface 'bat0'
	option proto 'batadv'
	option routing_algo 'BATMAN_IV'
	option gw_mode 'server'
	option gw_bandwidth '500000/500000'
	option hop_penalty '30'
	option orig_interval '1000'

config device 'bat0_vlan10'
	option type '8021q'
	option ifname 'bat0'
	option vid '10'
	option name 'bat0.10'

config interface 'mesh0'
	option proto 'batadv_hardif'
	option master 'bat0'
	option mtu '1532'

config device 'br_lan'
	option name 'br-lan'
	option type 'bridge'
	list ports 'lan1'
	list ports 'lan2'
	list ports 'lan3'
	list ports 'bat0.10'
"""
        return ""


def main():
    print("=" * 60)
    print("TESTING UCI SHOW FORMAT PARSER")
    print("=" * 60)

    config = UCIConfig()
    mock_ssh = MockSSH()

    # Parse the remote config
    remote_commands = config._parse_remote_config(mock_ssh)

    print(f"\n✓ Parsed {len(remote_commands)} commands from UCI show format\n")

    # Group by type
    by_action = {}
    for cmd in remote_commands:
        by_action[cmd.action] = by_action.get(cmd.action, 0) + 1

    print("Commands by action:")
    for action, count in sorted(by_action.items()):
        print(f"  {action}: {count}")

    # Show some examples
    print("\nSample section definitions:")
    sections = [cmd for cmd in remote_commands if cmd.action == "set" and len(cmd.path.split(".")) == 2]
    for cmd in sections[:5]:
        print(f"  {cmd.to_string()}")

    print("\nSample options:")
    options = [cmd for cmd in remote_commands if cmd.action == "set" and len(cmd.path.split(".")) == 3]
    for cmd in options[:5]:
        print(f"  {cmd.to_string()}")

    print("\nSample list items:")
    lists = [cmd for cmd in remote_commands if cmd.action == "add_list"]
    for cmd in lists[:5]:
        print(f"  {cmd.to_string()}")

    # Test diff
    print("\n" + "=" * 60)
    print("DIFF TEST (empty local config)")
    print("=" * 60)

    diff = config.diff(mock_ssh, show_remote_only=True)

    print(f"\nRemote-only commands: {len(diff.remote_only)}")
    print(f"Commands to add: {len(diff.to_add)}")
    print(f"Commands to modify: {len(diff.to_modify)}")

    if diff.remote_only:
        print("\n✓ SUCCESS! Remote-only detection working with UCI show format")
        print("\nTree view:")
        print(diff.to_tree())
    else:
        print("\n✗ FAILED! No remote-only commands detected")


if __name__ == "__main__":
    main()
