"""Tests for the main UCI configuration."""

import pytest
from wrtkit import UCIConfig


def test_config_to_script():
    """Test generating a complete configuration script."""
    from wrtkit.network import NetworkInterface
    from wrtkit.wireless import WirelessRadio
    from wrtkit.dhcp import DHCPSection
    from wrtkit.firewall import FirewallZone

    config = UCIConfig()

    lan = NetworkInterface("lan").with_device("eth0").with_proto("static").with_ipaddr("192.168.1.1")
    config.network.add_interface(lan)

    radio = WirelessRadio("radio0").with_channel(11).with_htmode("HT20")
    config.wireless.add_radio(radio)

    dhcp = DHCPSection("lan").with_interface("lan").with_start(100).with_limit(150)
    config.dhcp.add_dhcp(dhcp)

    zone = FirewallZone(0).with_name("lan").with_input("ACCEPT")
    config.firewall.add_zone(zone)

    script = config.to_script(include_commit=True, include_reload=True)

    assert "#!/bin/sh" in script
    assert "uci set network.lan='interface'" in script
    assert "uci set wireless.radio0='wifi-device'" in script
    assert "uci set dhcp.lan='dhcp'" in script
    assert "uci set firewall.@zone[0]='zone'" in script
    assert "uci commit" in script
    assert "/etc/init.d/network restart" in script
    assert "wifi reload" in script


def test_config_without_reload():
    """Test generating config without reload commands."""
    from wrtkit.network import NetworkInterface

    config = UCIConfig()
    lan = NetworkInterface("lan").with_device("eth0").with_proto("static")
    config.network.add_interface(lan)

    script = config.to_script(include_commit=False, include_reload=False)

    assert "uci commit" not in script
    assert "/etc/init.d/network restart" not in script
    assert "wifi reload" not in script


def test_get_all_commands():
    """Test getting all commands from all sections."""
    from wrtkit.network import NetworkInterface
    from wrtkit.wireless import WirelessRadio
    from wrtkit.dhcp import DHCPSection
    from wrtkit.firewall import FirewallZone

    config = UCIConfig()

    lan = NetworkInterface("lan").with_device("eth0")
    config.network.add_interface(lan)

    radio = WirelessRadio("radio0").with_channel(11)
    config.wireless.add_radio(radio)

    dhcp = DHCPSection("lan").with_interface("lan")
    config.dhcp.add_dhcp(dhcp)

    zone = FirewallZone(0).with_name("lan")
    config.firewall.add_zone(zone)

    commands = config.get_all_commands()

    # Should have commands from all sections
    assert any("network" in cmd.path for cmd in commands)
    assert any("wireless" in cmd.path for cmd in commands)
    assert any("dhcp" in cmd.path for cmd in commands)
    assert any("firewall" in cmd.path for cmd in commands)


def test_uci_command_to_string():
    """Test UCI command string generation."""
    from wrtkit.base import UCICommand

    cmd_set = UCICommand("set", "network.lan.ipaddr", "192.168.1.1")
    assert cmd_set.to_string() == "uci set network.lan.ipaddr='192.168.1.1'"

    cmd_list = UCICommand("add_list", "network.br_lan.ports", "lan1")
    assert cmd_list.to_string() == "uci add_list network.br_lan.ports='lan1'"

    cmd_delete = UCICommand("delete", "network.old_interface", None)
    assert cmd_delete.to_string() == "uci delete network.old_interface"


def test_config_diff_remote_only():
    """Test that diff tracks remote-only UCI settings."""
    from wrtkit.base import UCICommand
    from wrtkit.config import ConfigDiff

    diff = ConfigDiff()

    # Simulate remote-only settings
    diff.remote_only = [
        UCICommand("set", "network.guest.proto", "dhcp"),
        UCICommand("set", "wireless.radio1.channel", "36"),
    ]

    # Test that remote_only is included in string output
    output = str(diff)
    assert "Remote-only settings (not managed by config):" in output
    assert "network.guest.proto" in output
    assert "wireless.radio1.channel" in output

    # Test is_empty considers remote_only
    assert not diff.is_empty()


def test_config_diff_tree_format():
    """Test tree-structured diff output."""
    from wrtkit.base import UCICommand
    from wrtkit.config import ConfigDiff

    diff = ConfigDiff()

    # Add some changes
    diff.to_add = [
        UCICommand("set", "network.lan.ipaddr", "192.168.1.1"),
        UCICommand("set", "network.lan.netmask", "255.255.255.0"),
        UCICommand("set", "wireless.radio0.channel", "11"),
    ]

    diff.to_modify = [
        (
            UCICommand("set", "network.wan.proto", "static"),
            UCICommand("set", "network.wan.proto", "dhcp"),
        )
    ]

    diff.remote_only = [
        UCICommand("set", "network.guest.proto", "dhcp"),
    ]

    # Generate tree output
    tree_output = diff.to_tree()

    # Check that packages are organized
    assert "network/" in tree_output
    assert "wireless/" in tree_output

    # Check tree structure characters
    assert "├──" in tree_output or "└──" in tree_output

    # Check that changes are shown with appropriate symbols
    assert "+" in tree_output  # additions
    assert "~" in tree_output  # modifications
    assert "*" in tree_output  # remote-only
    assert "(remote-only)" in tree_output


def test_config_diff_grouping():
    """Test that commands are properly grouped by package and section."""
    from wrtkit.base import UCICommand
    from wrtkit.config import ConfigDiff

    diff = ConfigDiff()

    commands = [
        UCICommand("set", "network.lan.ipaddr", "192.168.1.1"),
        UCICommand("set", "network.lan.netmask", "255.255.255.0"),
        UCICommand("set", "network.wan.proto", "dhcp"),
        UCICommand("set", "wireless.radio0.channel", "11"),
        UCICommand("set", "wireless.radio0.htmode", "HT20"),
    ]

    grouped = diff._group_commands_by_resource(commands)

    # Check packages
    assert "network" in grouped
    assert "wireless" in grouped

    # Check sections
    assert "lan" in grouped["network"]
    assert "wan" in grouped["network"]
    assert "radio0" in grouped["wireless"]

    # Check command counts
    assert len(grouped["network"]["lan"]) == 2
    assert len(grouped["network"]["wan"]) == 1
    assert len(grouped["wireless"]["radio0"]) == 2


def test_config_diff_empty():
    """Test empty diff handling."""
    from wrtkit.config import ConfigDiff

    diff = ConfigDiff()

    assert diff.is_empty()
    # Note: str() now uses color by default, so we test to_string(color=False)
    assert diff.to_string(color=False) == "No differences found."
    assert diff.to_tree(color=False) == "No differences found."


def test_parse_uci_show_format():
    """Test parsing UCI show format (as opposed to UCI export format)."""
    from wrtkit import UCIConfig

    config = UCIConfig()

    # Sample UCI show format output
    uci_show_output = """package network

config interface 'loopback'
	option device 'lo'
	option proto 'static'
	list ipaddr '127.0.0.1/8'

config interface 'lan'
	option device 'br-lan'
	option proto 'static'
	option ipaddr '192.168.10.1'
	option netmask '255.255.255.0'

config device 'br_lan'
	option name 'br-lan'
	option type 'bridge'
	list ports 'lan1'
	list ports 'lan2'
"""

    commands = config._parse_uci_show_format("network", uci_show_output)

    # Should parse section definitions, options, and lists
    assert len(commands) > 0

    # Check section definitions
    sections = [cmd for cmd in commands if len(cmd.path.split(".")) == 2]
    assert len(sections) == 3  # loopback, lan, br_lan

    # Check options
    options = [cmd for cmd in commands if cmd.action == "set" and len(cmd.path.split(".")) == 3]
    assert len(options) >= 6  # Various options

    # Check list items
    lists = [cmd for cmd in commands if cmd.action == "add_list"]
    assert len(lists) == 3  # ipaddr list + 2 ports

    # Verify specific commands
    paths = [cmd.path for cmd in commands]
    assert "network.loopback" in paths
    assert "network.lan.ipaddr" in paths
    assert "network.br_lan.ports" in paths


def test_parse_uci_export_format():
    """Test parsing UCI export format."""
    from wrtkit import UCIConfig

    config = UCIConfig()

    # Sample UCI export format output
    uci_export_output = """network.loopback=interface
network.loopback.device='lo'
network.loopback.proto='static'
network.lan=interface
network.lan.device='br-lan'
network.lan.proto='static'
network.lan.ipaddr='192.168.10.1'
"""

    commands = config._parse_uci_export_format("network", uci_export_output)

    assert len(commands) == 7

    # Check section definitions
    sections = [cmd for cmd in commands if len(cmd.path.split(".")) == 2]
    assert len(sections) == 2  # loopback, lan

    # Check options
    options = [cmd for cmd in commands if len(cmd.path.split(".")) == 3]
    assert len(options) == 5  # device, proto, device, proto, ipaddr

    # Verify specific values
    ipaddr_cmd = next(cmd for cmd in commands if cmd.path == "network.lan.ipaddr")
    assert ipaddr_cmd.value == "192.168.10.1"


def test_config_diff_common_settings():
    """Test that diff tracks common settings between local and remote."""
    from wrtkit.base import UCICommand
    from wrtkit.config import ConfigDiff, UCIConfig

    # Create a mock SSH connection
    class MockSSH:
        def get_uci_config(self, package: str) -> str:
            if package == "network":
                return """network.lan=interface
network.lan.ipaddr='192.168.1.1'
network.lan.netmask='255.255.255.0'
network.wan=interface
network.wan.proto='dhcp'
network.guest=interface
network.guest.proto='static'"""
            return ""

    config = UCIConfig()
    # Add some local config that matches remote
    from wrtkit.network import NetworkInterface
    lan = NetworkInterface("lan")\
        .with_ipaddr("192.168.1.1")\
        .with_netmask("255.255.255.0")
    config.network.add_interface(lan)

    # Add some local config that differs from remote
    wan = NetworkInterface("wan").with_proto("static")
    config.network.add_interface(wan)

    # Get diff
    diff = config.diff(MockSSH(), show_remote_only=True)

    # Check that common settings are tracked
    assert len(diff.common) == 4  # lan section + ipaddr + netmask + wan section

    # Check that modifications are detected (wan.proto different)
    assert len(diff.to_modify) == 1
    assert diff.to_modify[0][1].path == "network.wan.proto"

    # Check that remote-only settings are tracked
    assert len(diff.remote_only) == 2  # guest section + guest.proto

    # Check summary includes common count
    summary = diff.to_string(color=False)
    assert "in common" in summary


def test_config_diff_list_items():
    """Test that diff correctly handles UCI list items (add_list commands)."""
    from wrtkit.config import UCIConfig

    # Create a mock SSH connection with list items
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
    # Add local config with some overlapping and some different list items
    from wrtkit.network import NetworkDevice
    device = NetworkDevice("br_lan")\
        .with_name("br-lan")\
        .with_type("bridge")\
        .with_port("lan1")\
        .with_port("bat0.10")
    config.network.add_device(device)

    # Get diff
    diff = config.diff(MockSSH(), show_remote_only=True)

    # Check that list items are correctly categorized
    # Should have: lan1 in common, bat0.10 to add, lan2 and lan3 as remote-only

    # Find the add_list commands
    to_add_ports = [cmd for cmd in diff.to_add if cmd.action == "add_list" and "ports" in cmd.path]
    remote_only_ports = [cmd for cmd in diff.remote_only if cmd.action == "add_list" and "ports" in cmd.path]
    common_ports = [cmd for cmd in diff.common if cmd.action == "add_list" and "ports" in cmd.path]

    # Verify list items
    assert len(to_add_ports) == 1
    assert to_add_ports[0].value == "bat0.10"

    assert len(remote_only_ports) == 2
    assert set(cmd.value for cmd in remote_only_ports) == {"lan2", "lan3"}

    assert len(common_ports) == 1
    assert common_ports[0].value == "lan1"

    # Also check that regular set commands still work (section definition, name, type)
    common_sets = [cmd for cmd in diff.common if cmd.action == "set"]
    assert len(common_sets) == 3  # br_lan section, name, type
