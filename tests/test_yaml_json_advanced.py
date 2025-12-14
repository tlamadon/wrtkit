"""Advanced tests for YAML/JSON functionality including edge cases and integration scenarios."""

import json
import tempfile
from pathlib import Path

from wrtkit.config import UCIConfig
from wrtkit.network import NetworkConfig, NetworkDevice, NetworkInterface
from wrtkit.wireless import WirelessConfig, WirelessRadio, WirelessInterface
from wrtkit.dhcp import DHCPConfig, DHCPSection
from wrtkit.firewall import FirewallConfig, FirewallZone, FirewallForwarding


def test_empty_config_serialization():
    """Test serializing an empty configuration."""
    config = UCIConfig()

    # Should produce empty dict
    data = config.to_dict()
    assert data == {}

    # Should produce empty YAML
    yaml_str = config.to_yaml()
    assert yaml_str.strip() in ["{}", ""]

    # Should be loadable
    restored = UCIConfig.from_yaml(yaml_str)
    assert len(restored.network.devices) == 0
    assert len(restored.network.interfaces) == 0


def test_list_fields_serialization():
    """Test that list fields are properly serialized."""
    device = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge") \
        .with_ports(["lan1", "lan2", "lan3", "lan4"])

    yaml_str = device.to_yaml()

    # Should contain list with correct items
    assert "ports:" in yaml_str
    assert "- lan1" in yaml_str
    assert "- lan2" in yaml_str
    assert "- lan3" in yaml_str
    assert "- lan4" in yaml_str

    # Restore and verify
    restored = NetworkDevice.from_yaml(yaml_str, "br_lan")
    assert restored.ports == ["lan1", "lan2", "lan3", "lan4"]


def test_boolean_serialization():
    """Test that boolean values are serialized correctly."""
    radio = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_disabled(False)

    # To YAML
    yaml_str = radio.to_yaml()
    assert "disabled: false" in yaml_str.lower()

    # To JSON
    json_str = radio.to_json()
    data = json.loads(json_str)
    assert data["disabled"] is False

    # Roundtrip
    restored = WirelessRadio.from_yaml(yaml_str, "radio0")
    assert restored.disabled is False


def test_integer_serialization():
    """Test that integer values are properly handled."""
    radio = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_txpower(20)

    dhcp = DHCPSection("lan") \
        .with_start(100) \
        .with_limit(150)

    # Check types are preserved
    radio_json = json.loads(radio.to_json())
    assert isinstance(radio_json["channel"], int)
    assert isinstance(radio_json["txpower"], int)

    dhcp_json = json.loads(dhcp.to_json())
    assert isinstance(dhcp_json["start"], int)
    assert isinstance(dhcp_json["limit"], int)


def test_special_characters_in_strings():
    """Test handling of special characters in string values."""
    interface = WirelessInterface("test") \
        .with_device("radio0") \
        .with_ssid("Test Network with 'quotes' and \"double quotes\"") \
        .with_key("Password!@#$%^&*()")

    # Serialize to YAML
    yaml_str = interface.to_yaml()

    # Restore
    restored = WirelessInterface.from_yaml(yaml_str, "test")
    assert restored.ssid == "Test Network with 'quotes' and \"double quotes\""
    assert restored.key == "Password!@#$%^&*()"


def test_unicode_characters():
    """Test handling of unicode characters."""
    interface = WirelessInterface("test") \
        .with_device("radio0") \
        .with_ssid("Tëst Nétwork 网络 🚀")

    yaml_str = interface.to_yaml()
    json_str = interface.to_json()

    # Restore from both
    from_yaml = WirelessInterface.from_yaml(yaml_str, "test")
    from_json = WirelessInterface.from_json(json_str, "test")

    assert from_yaml.ssid == "Tëst Nétwork 网络 🚀"
    assert from_json.ssid == "Tëst Nétwork 网络 🚀"


def test_nested_list_in_firewall():
    """Test that nested lists in firewall zones work correctly."""
    zone = FirewallZone(0) \
        .with_name("lan") \
        .with_networks(["lan", "guest", "iot"])

    config = UCIConfig()
    config.firewall.add_zone(zone)

    # Serialize
    yaml_str = config.to_yaml()

    # Should contain list
    assert "network:" in yaml_str
    assert "- lan" in yaml_str
    assert "- guest" in yaml_str
    assert "- iot" in yaml_str

    # Restore
    restored = UCIConfig.from_yaml(yaml_str)
    assert len(restored.firewall.zones) == 1
    assert set(restored.firewall.zones[0].network) == {"lan", "guest", "iot"}


def test_multiple_sections_same_type():
    """Test multiple sections of the same type."""
    config = UCIConfig()

    # Add multiple interfaces
    for i in range(5):
        interface = NetworkInterface(f"eth{i}") \
            .with_device(f"eth{i}") \
            .with_proto("dhcp")
        config.network.add_interface(interface)

    # Serialize
    yaml_str = config.to_yaml()

    # Restore
    restored = UCIConfig.from_yaml(yaml_str)
    assert len(restored.network.interfaces) == 5

    # Verify all interfaces
    section_names = {iface._section for iface in restored.network.interfaces}
    assert section_names == {"eth0", "eth1", "eth2", "eth3", "eth4"}


def test_hybrid_workflow():
    """Test combining YAML loading with programmatic additions."""
    # Create base config
    base_config = UCIConfig()
    device = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge") \
        .with_ports(["lan1", "lan2"])
    base_config.network.add_device(device)

    # Save to file
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_file = Path(tmpdir) / "base.yaml"
        base_config.to_yaml_file(str(yaml_file))

        # Load and extend
        loaded_config = UCIConfig.from_yaml_file(str(yaml_file))

        # Add more interfaces
        for vlan_id in [10, 20, 30]:
            interface = NetworkInterface(f"vlan{vlan_id}") \
                .with_device(f"lan1.{vlan_id}") \
                .with_static_ip(f"192.168.{vlan_id}.1", "255.255.255.0")
            loaded_config.network.add_interface(interface)

        # Verify
        assert len(loaded_config.network.devices) == 1
        assert len(loaded_config.network.interfaces) == 3

        # Save combined
        combined_file = Path(tmpdir) / "combined.yaml"
        loaded_config.to_yaml_file(str(combined_file))

        # Load again
        final_config = UCIConfig.from_yaml_file(str(combined_file))
        assert len(final_config.network.interfaces) == 3


def test_partial_config_merge():
    """Test merging partial configurations."""
    # Network config
    network_config = UCIConfig()
    lan = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_static_ip("192.168.1.1", "255.255.255.0")
    network_config.network.add_interface(lan)

    # Wireless config
    wireless_config = UCIConfig()
    radio = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_htmode("HE80")
    wireless_config.wireless.add_radio(radio)

    # Save separately
    with tempfile.TemporaryDirectory() as tmpdir:
        network_config.to_yaml_file(f"{tmpdir}/network.yaml")
        wireless_config.to_yaml_file(f"{tmpdir}/wireless.yaml")

        # Load and merge
        merged = UCIConfig()

        net_data = UCIConfig.from_yaml_file(f"{tmpdir}/network.yaml")
        for iface in net_data.network.interfaces:
            merged.network.add_interface(iface)

        wl_data = UCIConfig.from_yaml_file(f"{tmpdir}/wireless.yaml")
        for radio in wl_data.wireless.radios:
            merged.wireless.add_radio(radio)

        # Verify merge
        assert len(merged.network.interfaces) == 1
        assert len(merged.wireless.radios) == 1


def test_schema_includes_all_packages():
    """Test that generated schema includes all packages."""
    schema = UCIConfig.json_schema()

    assert "properties" in schema
    assert "network" in schema["properties"]
    assert "wireless" in schema["properties"]
    assert "dhcp" in schema["properties"]
    assert "firewall" in schema["properties"]

    # Check nested structure
    assert "devices" in schema["properties"]["network"]["properties"]
    assert "interfaces" in schema["properties"]["network"]["properties"]
    assert "radios" in schema["properties"]["wireless"]["properties"]


def test_yaml_comments_preserved_on_load():
    """Test that YAML can contain comments (they won't be preserved but shouldn't break)."""
    yaml_with_comments = """
# Network configuration
network:
  interfaces:
    lan:
      # LAN interface config
      device: br-lan
      proto: static
      ipaddr: 192.168.1.1  # Gateway IP
"""
    # Should load without errors
    config = UCIConfig.from_yaml(yaml_with_comments)
    assert len(config.network.interfaces) == 1
    assert config.network.interfaces[0].ipaddr == "192.168.1.1"


def test_large_configuration():
    """Test handling of large configurations with many sections."""
    config = UCIConfig()

    # Add many network interfaces
    for i in range(50):
        interface = NetworkInterface(f"iface{i}") \
            .with_device(f"eth{i}") \
            .with_proto("dhcp")
        config.network.add_interface(interface)

    # Add many wireless interfaces
    for i in range(50):
        iface = WirelessInterface(f"wl{i}") \
            .with_device(f"radio{i % 2}") \
            .with_mode("ap") \
            .with_ssid(f"Network{i}")
        config.wireless.add_interface(iface)

    # Serialize and deserialize
    yaml_str = config.to_yaml()
    json_str = config.to_json()

    restored_yaml = UCIConfig.from_yaml(yaml_str)
    restored_json = UCIConfig.from_json(json_str)

    assert len(restored_yaml.network.interfaces) == 50
    assert len(restored_yaml.wireless.interfaces) == 50
    assert len(restored_json.network.interfaces) == 50
    assert len(restored_json.wireless.interfaces) == 50


def test_config_validation():
    """Test that loading configs validates the data."""
    # Valid config should load
    valid_yaml = """
network:
  interfaces:
    lan:
      device: br-lan
      proto: static
      ipaddr: 192.168.1.1
"""
    config = UCIConfig.from_yaml(valid_yaml)
    assert config.network.interfaces[0].ipaddr == "192.168.1.1"


def test_to_dict_with_complex_nesting():
    """Test to_dict with complex nested structures."""
    config = UCIConfig()

    # Add complex configuration
    device = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge") \
        .with_ports(["lan1", "lan2"])
    config.network.add_device(device)

    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_static_ip("192.168.1.1", "255.255.255.0")
    config.network.add_interface(interface)

    zone = FirewallZone(0) \
        .with_name("lan") \
        .with_networks(["lan", "guest"])
    config.firewall.add_zone(zone)

    # Get dict
    data = config.to_dict()

    # Verify structure
    assert "network" in data
    assert "devices" in data["network"]
    assert "br_lan" in data["network"]["devices"]
    assert data["network"]["devices"]["br_lan"]["ports"] == ["lan1", "lan2"]

    assert "firewall" in data
    assert "zones" in data["firewall"]
    assert "lan" in data["firewall"]["zones"]
    assert "lan" in data["firewall"]["zones"]["lan"]["network"]


def test_individual_section_file_operations():
    """Test saving and loading individual sections to files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and save different section types
        interface = NetworkInterface("lan") \
            .with_device("br-lan") \
            .with_static_ip("192.168.1.1", "255.255.255.0")
        interface.to_yaml_file(f"{tmpdir}/interface.yaml")
        interface.to_json_file(f"{tmpdir}/interface.json")

        radio = WirelessRadio("radio0") \
            .with_channel(36) \
            .with_htmode("HE80")
        radio.to_yaml_file(f"{tmpdir}/radio.yaml")

        dhcp = DHCPSection("lan") \
            .with_interface("lan") \
            .with_range(100, 150, "12h")
        dhcp.to_json_file(f"{tmpdir}/dhcp.json")

        # Load them back
        loaded_interface_yaml = NetworkInterface.from_yaml_file(f"{tmpdir}/interface.yaml", "lan")
        loaded_interface_json = NetworkInterface.from_json_file(f"{tmpdir}/interface.json", "lan")
        loaded_radio = WirelessRadio.from_yaml_file(f"{tmpdir}/radio.yaml", "radio0")
        loaded_dhcp = DHCPSection.from_json_file(f"{tmpdir}/dhcp.json", "lan")

        # Verify
        assert loaded_interface_yaml.ipaddr == "192.168.1.1"
        assert loaded_interface_json.ipaddr == "192.168.1.1"
        assert loaded_radio.channel == 36
        assert loaded_dhcp.start == 100


def test_config_equality_after_roundtrip():
    """Test that configurations are functionally equal after roundtrip."""
    original = UCIConfig()

    # Build a complete config
    device = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge") \
        .with_ports(["lan1", "lan2"])
    original.network.add_device(device)

    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_static_ip("192.168.1.1", "255.255.255.0")
    original.network.add_interface(interface)

    radio = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_htmode("HE80")
    original.wireless.add_radio(radio)

    # Get UCI commands from original
    original_commands = original.get_all_commands()

    # Roundtrip through YAML
    yaml_str = original.to_yaml()
    from_yaml = UCIConfig.from_yaml(yaml_str)
    yaml_commands = from_yaml.get_all_commands()

    # Roundtrip through JSON
    json_str = original.to_json()
    from_json = UCIConfig.from_json(json_str)
    json_commands = from_json.get_all_commands()

    # Commands should be equivalent
    assert len(original_commands) == len(yaml_commands)
    assert len(original_commands) == len(json_commands)

    # Convert to sets of string representations for comparison
    original_cmds = {cmd.to_string() for cmd in original_commands}
    yaml_cmds = {cmd.to_string() for cmd in yaml_commands}
    json_cmds = {cmd.to_string() for cmd in json_commands}

    assert original_cmds == yaml_cmds
    assert original_cmds == json_cmds
