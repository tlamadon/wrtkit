"""Tests for firewall configuration."""

import pytest
from wrtkit.firewall import FirewallConfig
from wrtkit.base import UCICommand


def test_firewall_zone():
    """Test configuring a firewall zone."""
    fw = FirewallConfig()
    fw.zone(0).name("lan").input("ACCEPT").output("ACCEPT").forward("ACCEPT").add_network("lan")

    commands = fw.get_commands()

    assert commands[0] == UCICommand("set", "firewall.@zone[0]", "zone")
    assert any(cmd.path == "firewall.@zone[0].name" and cmd.value == "lan" for cmd in commands)
    assert any(cmd.path == "firewall.@zone[0].input" and cmd.value == "ACCEPT" for cmd in commands)
    assert any(cmd.path == "firewall.@zone[0].output" and cmd.value == "ACCEPT" for cmd in commands)
    assert any(cmd.path == "firewall.@zone[0].forward" and cmd.value == "ACCEPT" for cmd in commands)


def test_wan_zone_with_masq():
    """Test WAN zone with masquerading."""
    fw = FirewallConfig()
    fw.zone(1).name("wan").input("REJECT").masq(True).mtu_fix(True).add_network("wan")

    commands = fw.get_commands()

    assert any(cmd.path == "firewall.@zone[1].masq" and cmd.value == "1" for cmd in commands)
    assert any(cmd.path == "firewall.@zone[1].mtu_fix" and cmd.value == "1" for cmd in commands)


def test_zone_with_multiple_networks():
    """Test zone with multiple networks."""
    fw = FirewallConfig()
    fw.zone(0).name("lan").add_network("lan").add_network("guest")

    commands = fw.get_commands()

    network_commands = [cmd for cmd in commands if "network" in cmd.path]
    assert len(network_commands) == 2
    assert all(cmd.action == "add_list" for cmd in network_commands)


def test_forwarding_rule():
    """Test firewall forwarding rule."""
    fw = FirewallConfig()
    fw.forwarding(0).src("lan").dest("wan")

    commands = fw.get_commands()

    assert commands[0] == UCICommand("set", "firewall.@forwarding[0]", "forwarding")
    assert any(cmd.path == "firewall.@forwarding[0].src" and cmd.value == "lan" for cmd in commands)
    assert any(cmd.path == "firewall.@forwarding[0].dest" and cmd.value == "wan" for cmd in commands)
