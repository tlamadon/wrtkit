"""Tests for network configuration."""

from wrtkit.network import NetworkConfig, NetworkDevice, NetworkInterface, BridgeVLAN
from wrtkit.base import UCICommand


def test_device_creation():
    """Test creating a network device."""
    net = NetworkConfig()
    device = (
        NetworkDevice("br_lan")
        .with_name("br-lan")
        .with_type("bridge")
        .with_port("lan1")
        .with_port("lan2")
    )

    net.add_device(device)

    commands = net.get_commands()
    assert len(commands) == 5  # type, name, type, port1, port2

    assert commands[0] == UCICommand("set", "network.br_lan", "device")
    assert commands[1] == UCICommand("set", "network.br_lan.name", "br-lan")
    assert commands[2] == UCICommand("set", "network.br_lan.type", "bridge")


def test_interface_creation():
    """Test creating a network interface."""
    net = NetworkConfig()
    interface = (
        NetworkInterface("lan")
        .with_device("br-lan")
        .with_proto("static")
        .with_ipaddr("192.168.1.1")
        .with_netmask("255.255.255.0")
    )

    net.add_interface(interface)

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
    interface = (
        NetworkInterface("bat0")
        .with_proto("batadv")
        .with_routing_algo("BATMAN_IV")
        .with_gw_mode("server")
        .with_gw_bandwidth("10000/10000")
        .with_hop_penalty(30)
        .with_orig_interval(1000)
    )

    net.add_interface(interface)

    commands = net.get_commands()

    assert any(
        cmd.path == "network.bat0.routing_algo" and cmd.value == "BATMAN_IV" for cmd in commands
    )
    assert any(cmd.path == "network.bat0.gw_mode" and cmd.value == "server" for cmd in commands)
    assert any(cmd.path == "network.bat0.hop_penalty" and cmd.value == "30" for cmd in commands)


def test_vlan_device():
    """Test creating a VLAN device."""
    net = NetworkConfig()
    device = (
        NetworkDevice("bat0_vlan10")
        .with_type("8021q")
        .with_ifname("bat0")
        .with_vid(10)
        .with_name("bat0.10")
    )

    net.add_device(device)

    commands = net.get_commands()

    assert any(cmd.path == "network.bat0_vlan10.type" and cmd.value == "8021q" for cmd in commands)
    assert any(cmd.path == "network.bat0_vlan10.vid" and cmd.value == "10" for cmd in commands)


def test_bridge_vlan_creation():
    """Test creating a bridge VLAN configuration."""
    net = NetworkConfig()
    bridge_vlan = (
        BridgeVLAN("br_trunk_vlan10")
        .with_device("br-trunk")
        .with_vlan(10)
        .with_port("lan1:u*")
        .with_port("lan2:u*")
        .with_port("lan3:u*")
        .with_port("wds0:t")
    )

    net.add_bridge_vlan(bridge_vlan)

    commands = net.get_commands()

    # Check section type
    assert commands[0] == UCICommand("set", "network.br_trunk_vlan10", "bridge-vlan")
    # Check device
    assert any(
        cmd.path == "network.br_trunk_vlan10.device" and cmd.value == "br-trunk"
        for cmd in commands
    )
    # Check VLAN ID
    assert any(
        cmd.path == "network.br_trunk_vlan10.vlan" and cmd.value == "10" for cmd in commands
    )
    # Check ports (should be list items)
    port_commands = [cmd for cmd in commands if cmd.path == "network.br_trunk_vlan10.ports"]
    assert len(port_commands) == 4
    assert any(cmd.value == "lan1:u*" for cmd in port_commands)
    assert any(cmd.value == "lan2:u*" for cmd in port_commands)
    assert any(cmd.value == "lan3:u*" for cmd in port_commands)
    assert any(cmd.value == "wds0:t" for cmd in port_commands)


def test_bridge_vlan_with_ports_method():
    """Test creating a bridge VLAN using with_ports method."""
    net = NetworkConfig()
    bridge_vlan = (
        BridgeVLAN("br_trunk_vlan20")
        .with_device("br-trunk")
        .with_vlan(20)
        .with_ports(["lan1:u*", "lan2:u*", "wds0:t"])
    )

    net.add_bridge_vlan(bridge_vlan)

    commands = net.get_commands()

    # Check section type
    assert commands[0] == UCICommand("set", "network.br_trunk_vlan20", "bridge-vlan")
    # Check that all ports are present
    port_commands = [cmd for cmd in commands if cmd.path == "network.br_trunk_vlan20.ports"]
    assert len(port_commands) == 3
