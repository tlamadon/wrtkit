"""Tests for DHCP configuration."""

import pytest
from wrtkit.dhcp import DHCPConfig
from wrtkit.base import UCICommand


def test_dhcp_configuration():
    """Test configuring a DHCP server."""
    dhcp = DHCPConfig()
    dhcp.dhcp("lan").interface("lan").start(100).limit(150).leasetime("12h").ignore(False)

    commands = dhcp.get_commands()
    assert len(commands) == 6

    assert commands[0] == UCICommand("set", "dhcp.lan", "dhcp")
    assert any(cmd.path == "dhcp.lan.interface" and cmd.value == "lan" for cmd in commands)
    assert any(cmd.path == "dhcp.lan.start" and cmd.value == "100" for cmd in commands)
    assert any(cmd.path == "dhcp.lan.limit" and cmd.value == "150" for cmd in commands)
    assert any(cmd.path == "dhcp.lan.leasetime" and cmd.value == "12h" for cmd in commands)
    assert any(cmd.path == "dhcp.lan.ignore" and cmd.value == "0" for cmd in commands)


def test_dhcp_disabled():
    """Test disabling a DHCP server."""
    dhcp = DHCPConfig()
    dhcp.dhcp("guest").interface("guest").ignore(True)

    commands = dhcp.get_commands()

    assert any(cmd.path == "dhcp.guest.ignore" and cmd.value == "1" for cmd in commands)
