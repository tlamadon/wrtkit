"""Tests for DHCP configuration."""

from wrtkit.dhcp import DHCPConfig, DHCPSection, DHCPHost
from wrtkit.base import UCICommand


def test_dhcp_configuration():
    """Test configuring a DHCP server."""
    dhcp = DHCPConfig()
    section = (
        DHCPSection("lan")
        .with_interface("lan")
        .with_start(100)
        .with_limit(150)
        .with_leasetime("12h")
        .with_ignore(False)
    )
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
    section = DHCPSection("guest").with_interface("guest").with_ignore(True)
    dhcp.add_dhcp(section)

    commands = dhcp.get_commands()

    assert any(cmd.path == "dhcp.guest.ignore" and cmd.value == "1" for cmd in commands)


def test_dhcp_host_static_lease():
    """Test configuring a DHCP static lease (host)."""
    dhcp = DHCPConfig()
    host = (
        DHCPHost("printer")
        .with_mac("aa:bb:cc:dd:ee:ff")
        .with_ip("192.168.1.50")
        .with_name("printer")
    )
    dhcp.add_host(host)

    commands = dhcp.get_commands()
    assert len(commands) == 4

    assert commands[0] == UCICommand("set", "dhcp.printer", "host")
    assert any(
        cmd.path == "dhcp.printer.mac" and cmd.value == "aa:bb:cc:dd:ee:ff" for cmd in commands
    )
    assert any(cmd.path == "dhcp.printer.ip" and cmd.value == "192.168.1.50" for cmd in commands)
    assert any(cmd.path == "dhcp.printer.name" and cmd.value == "printer" for cmd in commands)


def test_dhcp_host_with_leasetime():
    """Test static lease with custom lease time."""
    host = (
        DHCPHost("nas")
        .with_mac("11:22:33:44:55:66")
        .with_ip("192.168.1.100")
        .with_leasetime("infinite")
    )

    commands = host.get_commands()

    assert commands[0] == UCICommand("set", "dhcp.nas", "host")
    assert any(cmd.path == "dhcp.nas.leasetime" and cmd.value == "infinite" for cmd in commands)


def test_dhcp_host_convenience_builder():
    """Test the with_static_lease convenience method."""
    host = DHCPHost("device").with_static_lease(
        mac="aa:bb:cc:dd:ee:ff", ip="192.168.1.200", name="mydevice"
    )

    assert host.mac == "aa:bb:cc:dd:ee:ff"
    assert host.ip == "192.168.1.200"
    assert host.name == "mydevice"


def test_dhcp_config_with_sections_and_hosts():
    """Test DHCP config with both server sections and static hosts."""
    dhcp = DHCPConfig()

    # Add DHCP server section
    section = DHCPSection("lan").with_interface("lan").with_start(100).with_limit(150)
    dhcp.add_dhcp(section)

    # Add static hosts
    host1 = DHCPHost("printer").with_static_lease("aa:bb:cc:dd:ee:ff", "192.168.1.50")
    host2 = DHCPHost("nas").with_static_lease("11:22:33:44:55:66", "192.168.1.51", "nas")
    dhcp.add_host(host1)
    dhcp.add_host(host2)

    commands = dhcp.get_commands()

    # Should have section commands + host commands
    assert any(cmd.path == "dhcp.lan" and cmd.value == "dhcp" for cmd in commands)
    assert any(cmd.path == "dhcp.printer" and cmd.value == "host" for cmd in commands)
    assert any(cmd.path == "dhcp.nas" and cmd.value == "host" for cmd in commands)


def test_dhcp_host_field_aliases():
    """Test that field aliases map old names to correct UCI option names."""
    # Create host with old field names (macaddr, ipaddr, hostname)
    # These should be aliased to the correct names (mac, ip, name)
    host = DHCPHost(
        "monoprice", macaddr="D4:AD:20:92:44:AA", ipaddr="192.168.10.99", hostname="monoprice-con"
    )

    commands = host.get_commands()

    # Should generate commands with CORRECT option names (mac, ip, name)
    assert any(
        cmd.path == "dhcp.monoprice.mac" and cmd.value == "D4:AD:20:92:44:AA" for cmd in commands
    )
    assert any(cmd.path == "dhcp.monoprice.ip" and cmd.value == "192.168.10.99" for cmd in commands)
    assert any(
        cmd.path == "dhcp.monoprice.name" and cmd.value == "monoprice-con" for cmd in commands
    )

    # Should NOT generate commands with wrong option names
    assert not any(cmd.path == "dhcp.monoprice.macaddr" for cmd in commands)
    assert not any(cmd.path == "dhcp.monoprice.ipaddr" for cmd in commands)
    assert not any(cmd.path == "dhcp.monoprice.hostname" for cmd in commands)

    # Verify the model fields are using correct names
    assert host.mac == "D4:AD:20:92:44:AA"
    assert host.ip == "192.168.10.99"
    assert host.name == "monoprice-con"
