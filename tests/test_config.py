"""Tests for the main UCI configuration."""

import pytest
from wrtkit import UCIConfig


def test_config_to_script():
    """Test generating a complete configuration script."""
    config = UCIConfig()

    config.network.interface("lan").device("eth0").proto("static").ipaddr("192.168.1.1")

    config.wireless.radio("radio0").channel(11).htmode("HT20")

    config.dhcp.dhcp("lan").interface("lan").start(100).limit(150)

    config.firewall.zone(0).name("lan").input("ACCEPT")

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
    config = UCIConfig()
    config.network.interface("lan").device("eth0").proto("static")

    script = config.to_script(include_commit=False, include_reload=False)

    assert "uci commit" not in script
    assert "/etc/init.d/network restart" not in script
    assert "wifi reload" not in script


def test_get_all_commands():
    """Test getting all commands from all sections."""
    config = UCIConfig()

    config.network.interface("lan").device("eth0")
    config.wireless.radio("radio0").channel(11)
    config.dhcp.dhcp("lan").interface("lan")
    config.firewall.zone(0).name("lan")

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
