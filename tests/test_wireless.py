"""Tests for wireless configuration."""

import pytest
from wrtkit.wireless import WirelessConfig
from wrtkit.base import UCICommand


def test_radio_configuration():
    """Test configuring a wireless radio."""
    wireless = WirelessConfig()
    wireless.radio("radio0").channel(11).htmode("HT20").country("US").disabled(False)

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
    wireless.wifi_iface("default_ap").device("radio0").mode("ap").network("lan").ssid(
        "TestNetwork"
    ).encryption("psk2").key("password123")

    commands = wireless.get_commands()

    assert commands[0] == UCICommand("set", "wireless.default_ap", "wifi-iface")
    assert any(cmd.path == "wireless.default_ap.mode" and cmd.value == "ap" for cmd in commands)
    assert any(cmd.path == "wireless.default_ap.ssid" and cmd.value == "TestNetwork" for cmd in commands)
    assert any(cmd.path == "wireless.default_ap.encryption" and cmd.value == "psk2" for cmd in commands)


def test_mesh_interface():
    """Test configuring a mesh interface."""
    wireless = WirelessConfig()
    wireless.wifi_iface("mesh0").device("radio1").mode("mesh").ifname("mesh0").mesh_id(
        "testmesh"
    ).encryption("sae").key("meshkey").mesh_fwding(False).mcast_rate(18000)

    commands = wireless.get_commands()

    assert any(cmd.path == "wireless.mesh0.mode" and cmd.value == "mesh" for cmd in commands)
    assert any(cmd.path == "wireless.mesh0.mesh_id" and cmd.value == "testmesh" for cmd in commands)
    assert any(cmd.path == "wireless.mesh0.mesh_fwding" and cmd.value == "0" for cmd in commands)
    assert any(cmd.path == "wireless.mesh0.mcast_rate" and cmd.value == "18000" for cmd in commands)


def test_80211r_configuration():
    """Test 802.11r fast roaming configuration."""
    wireless = WirelessConfig()
    wireless.wifi_iface("ap").device("radio0").mode("ap").ssid("test").ieee80211r(
        True
    ).ft_over_ds(True).ft_psk_generate_local(True)

    commands = wireless.get_commands()

    assert any(cmd.path == "wireless.ap.ieee80211r" and cmd.value == "1" for cmd in commands)
    assert any(cmd.path == "wireless.ap.ft_over_ds" and cmd.value == "1" for cmd in commands)
    assert any(
        cmd.path == "wireless.ap.ft_psk_generate_local" and cmd.value == "1" for cmd in commands
    )
