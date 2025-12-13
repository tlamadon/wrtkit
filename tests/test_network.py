"""Tests for network configuration."""

import pytest
from wrtkit.network import NetworkConfig
from wrtkit.base import UCICommand


def test_device_creation():
    """Test creating a network device."""
    net = NetworkConfig()
    net.device("br_lan").name("br-lan").type("bridge").add_port("lan1").add_port("lan2")

    commands = net.get_commands()
    assert len(commands) == 5  # type, name, type, port1, port2

    assert commands[0] == UCICommand("set", "network.br_lan", "device")
    assert commands[1] == UCICommand("set", "network.br_lan.name", "br-lan")
    assert commands[2] == UCICommand("set", "network.br_lan.type", "bridge")


def test_interface_creation():
    """Test creating a network interface."""
    net = NetworkConfig()
    net.interface("lan").device("br-lan").proto("static").ipaddr("192.168.1.1").netmask(
        "255.255.255.0"
    )

    commands = net.get_commands()
    assert len(commands) == 5

    assert commands[0] == UCICommand("set", "network.lan", "interface")
    assert commands[1] == UCICommand("set", "network.lan.device", "br-lan")
    assert commands[2] == UCICommand("set", "network.lan.proto", "static")
    assert commands[3] == UCICommand("set", "network.lan.ipaddr", "192.168.1.1")
    assert commands[4] == UCICommand("set", "network.lan.netmask", "255.255.255.0")


def test_batadv_interface():
    """Test creating a batman-adv interface."""
    net = NetworkConfig()
    net.interface("bat0").proto("batadv").routing_algo("BATMAN_IV").gw_mode(
        "server"
    ).gw_bandwidth("10000/10000").hop_penalty(30).orig_interval(1000)

    commands = net.get_commands()

    assert any(cmd.path == "network.bat0.routing_algo" and cmd.value == "BATMAN_IV" for cmd in commands)
    assert any(cmd.path == "network.bat0.gw_mode" and cmd.value == "server" for cmd in commands)
    assert any(cmd.path == "network.bat0.hop_penalty" and cmd.value == "30" for cmd in commands)


def test_vlan_device():
    """Test creating a VLAN device."""
    net = NetworkConfig()
    net.device("bat0_vlan10").type("8021q").ifname("bat0").vid(10).name("bat0.10")

    commands = net.get_commands()

    assert any(cmd.path == "network.bat0_vlan10.type" and cmd.value == "8021q" for cmd in commands)
    assert any(cmd.path == "network.bat0_vlan10.vid" and cmd.value == "10" for cmd in commands)
