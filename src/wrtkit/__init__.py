"""WRTKit - A Python library for managing OpenWRT configuration over SSH and serial."""

from .config import UCIConfig
from .ssh import SSHConnection
from .serial import SerialConnection
from .network import NetworkConfig, NetworkDevice, NetworkInterface
from .wireless import WirelessConfig, WirelessRadio, WirelessInterface
from .dhcp import DHCPConfig, DHCPSection
from .firewall import FirewallConfig, FirewallZone, FirewallForwarding
from .mesh import (
    Client,
    MeshNode,
    MeshNetwork,
    collect_node_info,
    collect_mesh_network,
    display_mesh_tree,
)

__version__ = "0.1.0"

__all__ = [
    "UCIConfig",
    "SSHConnection",
    "SerialConnection",
    "NetworkConfig",
    "NetworkDevice",
    "NetworkInterface",
    "WirelessConfig",
    "WirelessRadio",
    "WirelessInterface",
    "DHCPConfig",
    "DHCPSection",
    "FirewallConfig",
    "FirewallZone",
    "FirewallForwarding",
    # Mesh network info
    "Client",
    "MeshNode",
    "MeshNetwork",
    "collect_node_info",
    "collect_mesh_network",
    "display_mesh_tree",
]
