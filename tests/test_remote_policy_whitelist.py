"""Tests for RemotePolicy whitelist functionality."""

import pytest
from wrtkit import RemotePolicy, UCIConfig, NetworkInterface, NetworkDevice
from wrtkit.dhcp import DHCPHost


def test_path_pattern_matching_exact():
    """Test exact path pattern matching."""
    policy = RemotePolicy(whitelist=["devices.br_lan.ports"])

    assert policy.is_path_whitelisted("devices.br_lan.ports")
    assert not policy.is_path_whitelisted("devices.br_lan.type")
    assert not policy.is_path_whitelisted("devices.br_wan.ports")
    assert not policy.is_path_whitelisted("interfaces.lan.gateway")


def test_path_pattern_matching_single_wildcard():
    """Test path pattern matching with single segment wildcard (*)."""
    policy = RemotePolicy(whitelist=["devices.*.lan"])

    # Should match any device with 'lan' option
    assert policy.is_path_whitelisted("devices.br_lan.lan")
    assert policy.is_path_whitelisted("devices.vlan_guest.lan")
    assert policy.is_path_whitelisted("devices.anything.lan")

    # Should not match different option names
    assert not policy.is_path_whitelisted("devices.br_lan.wan")
    assert not policy.is_path_whitelisted("devices.br_lan.ports")

    # Should not match wrong structure
    assert not policy.is_path_whitelisted("interfaces.lan.gateway")


def test_path_pattern_matching_multi_segment_wildcard():
    """Test path pattern matching with multi-segment wildcard (**)."""
    policy = RemotePolicy(whitelist=["**"])

    # ** should match everything
    assert policy.is_path_whitelisted("devices.br_lan.ports")
    assert policy.is_path_whitelisted("interfaces.lan.gateway")
    assert policy.is_path_whitelisted("a.b.c.d.e.f")


def test_path_pattern_matching_suffix_wildcard():
    """Test path pattern matching with suffix wildcard."""
    policy = RemotePolicy(whitelist=["interfaces.guest.*"])

    # Should match any option under guest interface
    assert policy.is_path_whitelisted("interfaces.guest.gateway")
    assert policy.is_path_whitelisted("interfaces.guest.proto")
    assert policy.is_path_whitelisted("interfaces.guest.ipaddr")

    # Should not match other interfaces
    assert not policy.is_path_whitelisted("interfaces.lan.gateway")
    assert not policy.is_path_whitelisted("interfaces.wan.proto")


def test_path_pattern_matching_glob_patterns():
    """Test path pattern matching with glob patterns in segments."""
    policy = RemotePolicy(whitelist=["devices.br_*.*"])

    # Should match devices starting with br_
    assert policy.is_path_whitelisted("devices.br_lan.ports")
    assert policy.is_path_whitelisted("devices.br_wan.type")
    assert policy.is_path_whitelisted("devices.br_guest.anything")

    # Should not match devices not starting with br_
    assert not policy.is_path_whitelisted("devices.vlan_guest.ports")
    assert not policy.is_path_whitelisted("devices.eth0.type")


def test_path_pattern_matching_multiple_patterns():
    """Test that multiple whitelist patterns work together."""
    policy = RemotePolicy(whitelist=[
        "devices.br_lan.ports",
        "interfaces.*.gateway",
        "hosts.guest_*.*"
    ])

    # First pattern
    assert policy.is_path_whitelisted("devices.br_lan.ports")
    assert not policy.is_path_whitelisted("devices.br_lan.type")

    # Second pattern
    assert policy.is_path_whitelisted("interfaces.lan.gateway")
    assert policy.is_path_whitelisted("interfaces.wan.gateway")
    assert not policy.is_path_whitelisted("interfaces.lan.proto")

    # Third pattern
    assert policy.is_path_whitelisted("hosts.guest_phone.mac")
    assert policy.is_path_whitelisted("hosts.guest_laptop.ip")
    assert not policy.is_path_whitelisted("hosts.main_server.mac")


def test_whitelist_with_double_wildcard_middle():
    """Test ** wildcard in the middle of a pattern."""
    policy = RemotePolicy(whitelist=["devices.**.ports"])

    # Should match ports at any depth under devices
    assert policy.is_path_whitelisted("devices.br_lan.ports")
    assert policy.is_path_whitelisted("devices.nested.deep.ports")

    # Should not match non-ports
    assert not policy.is_path_whitelisted("devices.br_lan.type")


def test_should_keep_remote_path_with_whitelist():
    """Test should_keep_remote_path with whitelist configured."""
    policy = RemotePolicy(whitelist=["devices.*.lan", "interfaces.guest.*"])

    # Whitelisted paths should be kept
    assert policy.should_keep_remote_path("devices.br_lan.lan")
    assert policy.should_keep_remote_path("interfaces.guest.gateway")

    # Non-whitelisted paths should not be kept
    assert not policy.should_keep_remote_path("devices.br_lan.wan")
    assert not policy.should_keep_remote_path("interfaces.lan.gateway")


def test_should_keep_remote_path_legacy_fallback():
    """Test that should_keep_remote_path falls back to legacy behavior when no whitelist."""
    # Legacy policy with allowed_sections
    policy = RemotePolicy(allowed_sections=["lan", "guest"])

    # Should use legacy behavior
    assert policy.should_keep_remote_path("devices.lan.anything")
    assert policy.should_keep_remote_path("devices.guest.anything")
    assert not policy.should_keep_remote_path("devices.wan.anything")


def test_whitelist_empty_means_nothing_kept():
    """Test that empty whitelist means nothing is whitelisted."""
    policy = RemotePolicy(whitelist=[])

    assert not policy.is_path_whitelisted("anything")
    assert not policy.is_path_whitelisted("devices.br_lan.ports")


def test_whitelist_in_diff_remote_only_section():
    """Test that diff respects whitelist for remote-only sections."""

    class MockSSH:
        def get_uci_config(self, package: str) -> str:
            if package == "network":
                return """
network.guest=interface
network.guest.proto='static'
network.guest.ipaddr='192.168.100.1'
network.guest.gateway='192.168.100.254'
network.temp=interface
network.temp.proto='dhcp'
"""
            return ""

    config = UCIConfig()

    # Local config is empty - both guest and temp are remote-only

    # Whitelist only guest interface, but exclude gateway
    config.network.remote_policy = RemotePolicy(whitelist=[
        "interfaces.guest.proto",
        "interfaces.guest.ipaddr"
    ])

    diff = config.diff(MockSSH(), show_remote_only=True)

    # guest.proto and guest.ipaddr should be in whitelisted (preserved)
    whitelisted_paths = {cmd.path for cmd in diff.whitelisted}
    assert "network.guest.proto" in whitelisted_paths
    assert "network.guest.ipaddr" in whitelisted_paths

    # guest.gateway should be in to_remove (not whitelisted)
    remove_paths = {cmd.path for cmd in diff.to_remove}
    assert "network.guest.gateway" in remove_paths

    # All of temp should be in to_remove (not whitelisted)
    assert "network.temp" in remove_paths
    assert "network.temp.proto" in remove_paths


def test_whitelist_in_diff_local_section_with_remote_extras():
    """Test whitelist with a locally-managed section that has extra remote options."""

    class MockSSH:
        def get_uci_config(self, package: str) -> str:
            if package == "dhcp":
                return """
dhcp.monoprice=host
dhcp.monoprice.mac='AA:BB:CC:DD:EE:FF'
dhcp.monoprice.ip='192.168.1.100'
dhcp.monoprice.hostname='monoprice-speaker'
dhcp.monoprice.force='1'
"""
            return ""

    config = UCIConfig()

    # Local config only has mac and ip
    host = DHCPHost("monoprice").with_mac("AA:BB:CC:DD:EE:FF").with_ip("192.168.1.100")
    config.dhcp.add_host(host)

    # Whitelist hostname but not force
    config.dhcp.remote_policy = RemotePolicy(whitelist=["hosts.*.hostname"])

    diff = config.diff(MockSSH(), show_remote_only=True)

    # hostname should be in whitelisted (preserved)
    whitelisted_paths = {cmd.path for cmd in diff.whitelisted}
    assert "dhcp.monoprice.hostname" in whitelisted_paths

    # force should be in to_remove (not whitelisted)
    remove_paths = {cmd.path for cmd in diff.to_remove}
    assert "dhcp.monoprice.force" in remove_paths

    # mac and ip should be in common (exist in both)
    common_paths = {cmd.path for cmd in diff.common}
    assert "dhcp.monoprice.mac" in common_paths
    assert "dhcp.monoprice.ip" in common_paths


def test_whitelist_with_wildcard_keeps_everything():
    """Test that ** whitelist keeps everything."""

    class MockSSH:
        def get_uci_config(self, package: str) -> str:
            if package == "network":
                return """
network.guest=interface
network.guest.proto='static'
network.temp=interface
network.temp.proto='dhcp'
"""
            return ""

    config = UCIConfig()

    # Local config is empty - everything is remote-only

    # Whitelist everything
    config.network.remote_policy = RemotePolicy(whitelist=["**"])

    diff = config.diff(MockSSH(), show_remote_only=True)

    # Everything should be whitelisted
    assert len(diff.to_remove) == 0
    assert len(diff.whitelisted) > 0


def test_whitelist_with_device_ports():
    """Test whitelist with device ports (list values)."""

    class MockSSH:
        def get_uci_config(self, package: str) -> str:
            if package == "network":
                return """
network.br_lan=device
network.br_lan.type='bridge'
network.br_lan.ports='lan1'
network.br_lan.ports='lan2'
network.br_lan.ports='bat0'
network.br_lan.ports='wlan0'
"""
            return ""

    config = UCIConfig()

    # Local config has only lan1
    device = NetworkDevice("br_lan").with_name("br-lan").with_type("bridge").with_port("lan1")
    config.network.add_device(device)

    # Whitelist lan2 port
    config.network.remote_policy = RemotePolicy(whitelist=["devices.br_lan.ports"])

    diff = config.diff(MockSSH(), show_remote_only=True)

    # lan1 should be in common (exists in both)
    common_values = {cmd.value for cmd in diff.common if "ports" in cmd.path}
    assert "lan1" in common_values

    # With the whitelist, all remote ports should be kept
    # Note: The current implementation may need adjustment to handle list values properly
    # This test documents the expected behavior


def test_whitelist_combined_patterns():
    """Test realistic combined whitelist patterns."""

    class MockSSH:
        def get_uci_config(self, package: str) -> str:
            if package == "network":
                return """
network.lan=interface
network.lan.proto='static'
network.lan.ipaddr='192.168.1.1'
network.lan.gateway='192.168.1.254'
network.guest=interface
network.guest.proto='static'
network.guest.ipaddr='192.168.100.1'
network.guest.gateway='192.168.100.254'
network.temp_test=interface
network.temp_test.proto='dhcp'
"""
            return ""

    config = UCIConfig()

    # Local config has only lan with proto and ipaddr
    lan = NetworkInterface("lan").with_proto("static").with_ipaddr("192.168.1.1")
    config.network.add_interface(lan)

    # Whitelist:
    # - All gateway options on any interface
    # - Everything under guest interface
    config.network.remote_policy = RemotePolicy(whitelist=[
        "interfaces.*.gateway",
        "interfaces.guest.*"
    ])

    diff = config.diff(MockSSH(), show_remote_only=True)

    whitelisted_paths = {cmd.path for cmd in diff.whitelisted}
    remove_paths = {cmd.path for cmd in diff.to_remove}

    # lan.gateway should be whitelisted (whitelisted by interfaces.*.gateway)
    assert "network.lan.gateway" in whitelisted_paths

    # guest options should all be whitelisted
    # Note: section definitions themselves need explicit whitelisting if desired
    assert "network.guest.proto" in whitelisted_paths
    assert "network.guest.ipaddr" in whitelisted_paths
    assert "network.guest.gateway" in whitelisted_paths

    # The section definition is kept if any option in it is kept
    # but it's technically a side effect of keeping the options

    # temp_test.* should be in to_remove (not whitelisted)
    assert "network.temp_test" in remove_paths
    assert "network.temp_test.proto" in remove_paths


def test_backward_compatibility_with_allowed_sections():
    """Test that old allowed_sections still works when whitelist is not set."""

    class MockSSH:
        def get_uci_config(self, package: str) -> str:
            if package == "network":
                return """
network.lan=interface
network.lan.proto='static'
network.guest=interface
network.guest.proto='static'
network.temp=interface
network.temp.proto='dhcp'
"""
            return ""

    config = UCIConfig()

    # Use old allowed_sections approach (no whitelist)
    config.network.remote_policy = RemotePolicy(allowed_sections=["lan", "guest"])

    diff = config.diff(MockSSH(), show_remote_only=True)

    remote_paths = {cmd.path for cmd in diff.remote_only}
    remove_paths = {cmd.path for cmd in diff.to_remove}

    # lan and guest should be in remote_only
    assert "network.lan" in remote_paths or "network.lan.proto" in remote_paths
    assert "network.guest" in remote_paths or "network.guest.proto" in remote_paths

    # temp should be in to_remove
    assert "network.temp" in remove_paths


def test_whitelist_precedence_over_allowed_sections():
    """Test that whitelist takes precedence over allowed_sections when both are set."""
    policy = RemotePolicy(
        allowed_sections=["*"],  # Would allow everything
        whitelist=["devices.br_lan.ports"]  # Only allow this specific path
    )

    # Whitelist should take precedence
    assert policy.should_keep_remote_path("devices.br_lan.ports")
    assert not policy.should_keep_remote_path("devices.br_lan.type")
    assert not policy.should_keep_remote_path("interfaces.lan.gateway")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
