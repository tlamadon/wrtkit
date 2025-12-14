"""Tests for YAML/JSON serialization and schema generation."""

import json
import tempfile
from pathlib import Path

from wrtkit.config import UCIConfig
from wrtkit.network import NetworkConfig, NetworkDevice, NetworkInterface
from wrtkit.wireless import WirelessConfig, WirelessRadio, WirelessInterface
from wrtkit.dhcp import DHCPConfig, DHCPSection
from wrtkit.firewall import FirewallConfig, FirewallZone, FirewallForwarding


def test_network_interface_to_yaml():
    """Test converting a network interface to YAML."""
    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static") \
        .with_ipaddr("192.168.1.1") \
        .with_netmask("255.255.255.0")

    yaml_str = interface.to_yaml()

    assert "device: br-lan" in yaml_str
    assert "proto: static" in yaml_str
    assert "ipaddr: 192.168.1.1" in yaml_str
    assert "netmask: 255.255.255.0" in yaml_str
    # Should not contain private fields
    assert "_section" not in yaml_str
    assert "_package" not in yaml_str


def test_network_interface_to_json():
    """Test converting a network interface to JSON."""
    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static") \
        .with_ipaddr("192.168.1.1")

    json_str = interface.to_json()
    data = json.loads(json_str)

    assert data["device"] == "br-lan"
    assert data["proto"] == "static"
    assert data["ipaddr"] == "192.168.1.1"
    # Should not contain private fields
    assert "_section" not in data
    assert "_package" not in data


def test_network_interface_from_yaml():
    """Test creating a network interface from YAML."""
    yaml_str = """
device: br-lan
proto: static
ipaddr: 192.168.1.1
netmask: 255.255.255.0
"""
    interface = NetworkInterface.from_yaml(yaml_str, "lan")

    assert interface._section == "lan"
    assert interface.device == "br-lan"
    assert interface.proto == "static"
    assert interface.ipaddr == "192.168.1.1"
    assert interface.netmask == "255.255.255.0"


def test_network_interface_from_json():
    """Test creating a network interface from JSON."""
    json_str = """{
  "device": "br-lan",
  "proto": "static",
  "ipaddr": "192.168.1.1",
  "netmask": "255.255.255.0"
}"""
    interface = NetworkInterface.from_json(json_str, "lan")

    assert interface._section == "lan"
    assert interface.device == "br-lan"
    assert interface.proto == "static"
    assert interface.ipaddr == "192.168.1.1"
    assert interface.netmask == "255.255.255.0"


def test_network_interface_yaml_roundtrip():
    """Test YAML serialization roundtrip."""
    original = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static") \
        .with_ipaddr("192.168.1.1") \
        .with_netmask("255.255.255.0")

    yaml_str = original.to_yaml()
    restored = NetworkInterface.from_yaml(yaml_str, "lan")

    assert original.device == restored.device
    assert original.proto == restored.proto
    assert original.ipaddr == restored.ipaddr
    assert original.netmask == restored.netmask


def test_wireless_radio_to_yaml():
    """Test converting a wireless radio to YAML."""
    radio = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_htmode("HE80") \
        .with_country("US")

    yaml_str = radio.to_yaml()

    assert "channel: 36" in yaml_str
    assert "htmode: HE80" in yaml_str
    assert "country: US" in yaml_str


def test_wireless_interface_from_yaml():
    """Test creating a wireless interface from YAML."""
    yaml_str = """
device: radio0
mode: ap
network: lan
ssid: TestNetwork
encryption: sae
key: TestPassword123
"""
    interface = WirelessInterface.from_yaml(yaml_str, "default_radio0")

    assert interface._section == "default_radio0"
    assert interface.device == "radio0"
    assert interface.mode == "ap"
    assert interface.ssid == "TestNetwork"
    assert interface.encryption == "sae"
    assert interface.key == "TestPassword123"


def test_uciconfig_to_yaml():
    """Test converting a complete UCI configuration to YAML."""
    config = UCIConfig()

    # Add network configuration
    device = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge") \
        .with_ports(["lan1", "lan2"])
    config.network.add_device(device)

    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static") \
        .with_ipaddr("192.168.1.1") \
        .with_netmask("255.255.255.0")
    config.network.add_interface(interface)

    # Add wireless configuration
    radio = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_htmode("HE80") \
        .with_country("US")
    config.wireless.add_radio(radio)

    # Add DHCP configuration
    dhcp = DHCPSection("lan") \
        .with_interface("lan") \
        .with_range(100, 150, "12h")
    config.dhcp.add_dhcp(dhcp)

    yaml_str = config.to_yaml()

    assert "network:" in yaml_str
    assert "devices:" in yaml_str
    assert "br_lan:" in yaml_str
    assert "wireless:" in yaml_str
    assert "radios:" in yaml_str
    assert "radio0:" in yaml_str
    assert "dhcp:" in yaml_str


def test_uciconfig_to_json():
    """Test converting a complete UCI configuration to JSON."""
    config = UCIConfig()

    device = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge")
    config.network.add_device(device)

    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static") \
        .with_ipaddr("192.168.1.1")
    config.network.add_interface(interface)

    json_str = config.to_json()
    data = json.loads(json_str)

    assert "network" in data
    assert "devices" in data["network"]
    assert "br_lan" in data["network"]["devices"]
    assert data["network"]["devices"]["br_lan"]["name"] == "br-lan"
    assert data["network"]["devices"]["br_lan"]["type"] == "bridge"


def test_uciconfig_from_yaml():
    """Test creating a UCI configuration from YAML."""
    yaml_str = """
network:
  devices:
    br_lan:
      name: br-lan
      type: bridge
      ports:
        - lan1
        - lan2
  interfaces:
    lan:
      device: br-lan
      proto: static
      ipaddr: 192.168.1.1
      netmask: 255.255.255.0

wireless:
  radios:
    radio0:
      channel: 36
      htmode: HE80
      country: US
  interfaces:
    default_radio0:
      device: radio0
      mode: ap
      ssid: TestNetwork

dhcp:
  sections:
    lan:
      interface: lan
      start: 100
      limit: 150
      leasetime: 12h
"""
    config = UCIConfig.from_yaml(yaml_str)

    # Check network configuration
    assert len(config.network.devices) == 1
    assert config.network.devices[0]._section == "br_lan"
    assert config.network.devices[0].name == "br-lan"
    assert config.network.devices[0].type == "bridge"
    assert config.network.devices[0].ports == ["lan1", "lan2"]

    assert len(config.network.interfaces) == 1
    assert config.network.interfaces[0]._section == "lan"
    assert config.network.interfaces[0].device == "br-lan"
    assert config.network.interfaces[0].proto == "static"
    assert config.network.interfaces[0].ipaddr == "192.168.1.1"

    # Check wireless configuration
    assert len(config.wireless.radios) == 1
    assert config.wireless.radios[0]._section == "radio0"
    assert config.wireless.radios[0].channel == 36
    assert config.wireless.radios[0].htmode == "HE80"

    assert len(config.wireless.interfaces) == 1
    assert config.wireless.interfaces[0]._section == "default_radio0"
    assert config.wireless.interfaces[0].device == "radio0"
    assert config.wireless.interfaces[0].mode == "ap"

    # Check DHCP configuration
    assert len(config.dhcp.sections) == 1
    assert config.dhcp.sections[0]._section == "lan"
    assert config.dhcp.sections[0].interface == "lan"
    assert config.dhcp.sections[0].start == 100
    assert config.dhcp.sections[0].limit == 150


def test_uciconfig_from_json():
    """Test creating a UCI configuration from JSON."""
    json_str = """{
  "network": {
    "devices": {
      "br_lan": {
        "name": "br-lan",
        "type": "bridge",
        "ports": ["lan1", "lan2"]
      }
    },
    "interfaces": {
      "lan": {
        "device": "br-lan",
        "proto": "static",
        "ipaddr": "192.168.1.1"
      }
    }
  }
}"""
    config = UCIConfig.from_json(json_str)

    assert len(config.network.devices) == 1
    assert config.network.devices[0]._section == "br_lan"
    assert config.network.devices[0].name == "br-lan"
    assert config.network.devices[0].type == "bridge"

    assert len(config.network.interfaces) == 1
    assert config.network.interfaces[0]._section == "lan"
    assert config.network.interfaces[0].proto == "static"


def test_uciconfig_yaml_roundtrip():
    """Test complete YAML serialization roundtrip."""
    # Create original configuration
    original = UCIConfig()

    device = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge") \
        .with_ports(["lan1", "lan2"])
    original.network.add_device(device)

    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static") \
        .with_ipaddr("192.168.1.1") \
        .with_netmask("255.255.255.0")
    original.network.add_interface(interface)

    radio = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_htmode("HE80")
    original.wireless.add_radio(radio)

    # Serialize to YAML and deserialize
    yaml_str = original.to_yaml()
    restored = UCIConfig.from_yaml(yaml_str)

    # Verify network configuration
    assert len(restored.network.devices) == 1
    assert restored.network.devices[0].name == "br-lan"
    assert restored.network.devices[0].type == "bridge"
    assert restored.network.devices[0].ports == ["lan1", "lan2"]

    assert len(restored.network.interfaces) == 1
    assert restored.network.interfaces[0].device == "br-lan"
    assert restored.network.interfaces[0].proto == "static"

    # Verify wireless configuration
    assert len(restored.wireless.radios) == 1
    assert restored.wireless.radios[0].channel == 36
    assert restored.wireless.radios[0].htmode == "HE80"


def test_file_operations():
    """Test reading and writing YAML/JSON files."""
    config = UCIConfig()

    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static") \
        .with_ipaddr("192.168.1.1")
    config.network.add_interface(interface)

    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_file = Path(tmpdir) / "config.yaml"
        json_file = Path(tmpdir) / "config.json"

        # Test YAML file operations
        config.to_yaml_file(str(yaml_file))
        assert yaml_file.exists()
        loaded_from_yaml = UCIConfig.from_yaml_file(str(yaml_file))
        assert len(loaded_from_yaml.network.interfaces) == 1
        assert loaded_from_yaml.network.interfaces[0].ipaddr == "192.168.1.1"

        # Test JSON file operations
        config.to_json_file(str(json_file))
        assert json_file.exists()
        loaded_from_json = UCIConfig.from_json_file(str(json_file))
        assert len(loaded_from_json.network.interfaces) == 1
        assert loaded_from_json.network.interfaces[0].ipaddr == "192.168.1.1"


def test_network_interface_json_schema():
    """Test generating JSON schema for NetworkInterface."""
    schema = NetworkInterface.json_schema()

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "device" in schema["properties"]
    assert "proto" in schema["properties"]
    assert "ipaddr" in schema["properties"]


def test_uciconfig_json_schema():
    """Test generating JSON schema for complete UCI config."""
    schema = UCIConfig.json_schema()

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "network" in schema["properties"]
    assert "wireless" in schema["properties"]
    assert "dhcp" in schema["properties"]
    assert "firewall" in schema["properties"]


def test_uciconfig_yaml_schema():
    """Test generating YAML schema for complete UCI config."""
    schema_yaml = UCIConfig.yaml_schema()

    assert "type: object" in schema_yaml
    assert "properties:" in schema_yaml
    assert "network:" in schema_yaml
    assert "wireless:" in schema_yaml


def test_firewall_configuration():
    """Test firewall configuration serialization."""
    config = UCIConfig()

    zone = FirewallZone(0) \
        .with_name("lan") \
        .with_input("ACCEPT") \
        .with_output("ACCEPT") \
        .with_forward("ACCEPT") \
        .with_network("lan")
    config.firewall.add_zone(zone)

    forwarding = FirewallForwarding(0) \
        .with_src("lan") \
        .with_dest("wan")
    config.firewall.add_forwarding(forwarding)

    yaml_str = config.to_yaml()
    assert "firewall:" in yaml_str
    assert "zones:" in yaml_str
    assert "forwardings:" in yaml_str

    # Test roundtrip
    restored = UCIConfig.from_yaml(yaml_str)
    assert len(restored.firewall.zones) == 1
    assert restored.firewall.zones[0].name == "lan"
    assert len(restored.firewall.forwardings) == 1
    assert restored.firewall.forwardings[0].src == "lan"


def test_exclude_none_behavior():
    """Test that None values are excluded by default."""
    interface = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_proto("static")
    # ipaddr, netmask, gateway, etc. should be None

    yaml_str = interface.to_yaml(exclude_none=True)
    assert "device: br-lan" in yaml_str
    assert "proto: static" in yaml_str
    # None values should not appear
    assert "ipaddr" not in yaml_str
    assert "netmask" not in yaml_str
    assert "gateway" not in yaml_str


def test_permissive_schema():
    """Test that unknown fields are accepted (permissive schema)."""
    yaml_str = """
device: br-lan
proto: static
ipaddr: 192.168.1.1
custom_field: custom_value
another_unknown: 123
"""
    # This should not raise an error due to extra="allow" in Pydantic config
    interface = NetworkInterface.from_yaml(yaml_str, "lan")

    assert interface.device == "br-lan"
    assert interface.proto == "static"
    assert interface.ipaddr == "192.168.1.1"
    # Custom fields should be accessible via model_dump
    data = interface.model_dump()
    assert data["custom_field"] == "custom_value"
    assert data["another_unknown"] == 123
