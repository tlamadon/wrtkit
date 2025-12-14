"""Tests for DHCP configuration."""

from wrtkit.dhcp import DHCPConfig, DHCPSection
from wrtkit.base import UCICommand


def test_dhcp_configuration():
    """Test configuring a DHCP server."""
    dhcp = DHCPConfig()
    section = DHCPSection("lan")\
        .with_interface("lan")\
        .with_start(100)\
        .with_limit(150)\
        .with_leasetime("12h")\
        .with_ignore(False)
    dhcp.add_dhcp(section)

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
    section = DHCPSection("guest")\
        .with_interface("guest")\
        .with_ignore(True)
    dhcp.add_dhcp(section)

    commands = dhcp.get_commands()

    assert any(cmd.path == "dhcp.guest.ignore" and cmd.value == "1" for cmd in commands)
