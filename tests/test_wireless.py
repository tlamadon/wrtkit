"""Tests for wireless configuration."""

from wrtkit.wireless import WirelessConfig, WirelessRadio, WirelessInterface
from wrtkit.base import UCICommand


def test_radio_configuration():
    """Test configuring a wireless radio."""
    wireless = WirelessConfig()
    radio = (
        WirelessRadio("radio0")
        .with_channel(11)
        .with_htmode("HT20")
        .with_country("US")
        .with_disabled(False)
    )
    wireless.add_radio(radio)

    commands = wireless.get_commands()
    assert len(commands) == 5

    assert commands[0] == UCICommand("set", "wireless.radio0", "wifi-device")
    assert any(cmd.path == "wireless.radio0.channel" and cmd.value == "11" for cmd in commands)
    assert any(cmd.path == "wireless.radio0.htmode" and cmd.value == "HT20" for cmd in commands)
    assert any(cmd.path == "wireless.radio0.country" and cmd.value == "US" for cmd in commands)
    assert any(cmd.path == "wireless.radio0.disabled" and cmd.value == "0" for cmd in commands)


def test_ap_interface():
    """Test configuring an AP interface."""
    wireless = WirelessConfig()
    iface = (
        WirelessInterface("default_ap")
        .with_device("radio0")
        .with_mode("ap")
        .with_network("lan")
        .with_ssid("TestNetwork")
        .with_encryption("psk2")
        .with_key("password123")
    )
    wireless.add_interface(iface)

    commands = wireless.get_commands()

    assert commands[0] == UCICommand("set", "wireless.default_ap", "wifi-iface")
    assert any(cmd.path == "wireless.default_ap.mode" and cmd.value == "ap" for cmd in commands)
    assert any(
        cmd.path == "wireless.default_ap.ssid" and cmd.value == "TestNetwork" for cmd in commands
    )
    assert any(
        cmd.path == "wireless.default_ap.encryption" and cmd.value == "psk2" for cmd in commands
    )


def test_mesh_interface():
    """Test configuring a mesh interface."""
    wireless = WirelessConfig()
    iface = (
        WirelessInterface("mesh0")
        .with_device("radio1")
        .with_mode("mesh")
        .with_ifname("mesh0")
        .with_mesh_id("testmesh")
        .with_encryption("sae")
        .with_key("meshkey")
        .with_mesh_fwding(False)
        .with_mcast_rate(18000)
    )
    wireless.add_interface(iface)

    commands = wireless.get_commands()

    assert any(cmd.path == "wireless.mesh0.mode" and cmd.value == "mesh" for cmd in commands)
    assert any(cmd.path == "wireless.mesh0.mesh_id" and cmd.value == "testmesh" for cmd in commands)
    assert any(cmd.path == "wireless.mesh0.mesh_fwding" and cmd.value == "0" for cmd in commands)
    assert any(cmd.path == "wireless.mesh0.mcast_rate" and cmd.value == "18000" for cmd in commands)


def test_80211r_configuration():
    """Test 802.11r fast roaming configuration."""
    wireless = WirelessConfig()
    iface = (
        WirelessInterface("ap")
        .with_device("radio0")
        .with_mode("ap")
        .with_ssid("test")
        .with_ieee80211r(True)
        .with_ft_over_ds(True)
        .with_ft_psk_generate_local(True)
    )
    wireless.add_interface(iface)

    commands = wireless.get_commands()

    assert any(cmd.path == "wireless.ap.ieee80211r" and cmd.value == "1" for cmd in commands)
    assert any(cmd.path == "wireless.ap.ft_over_ds" and cmd.value == "1" for cmd in commands)
    assert any(
        cmd.path == "wireless.ap.ft_psk_generate_local" and cmd.value == "1" for cmd in commands
    )
