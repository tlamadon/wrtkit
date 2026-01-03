"""WRTKit - A Python library for managing OpenWRT configuration over SSH and serial."""

from .config import UCIConfig
from .ssh import SSHConnection
from .serial_connection import SerialConnection
from .network import NetworkConfig, NetworkDevice, NetworkInterface
from .wireless import WirelessConfig, WirelessRadio, WirelessInterface
from .dhcp import DHCPConfig, DHCPSection, DHCPHost
from .firewall import FirewallConfig, FirewallZone, FirewallForwarding
from .sqm import SQMConfig, SQMQueue
from .mesh import (
    Client,
    MeshNode,
    MeshNetwork,
    collect_node_info,
    collect_mesh_network,
    display_mesh_tree,
)
from .progress import Spinner, ProgressBar, spinner, progress_bar

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
    "DHCPHost",
    "FirewallConfig",
    "FirewallZone",
    "FirewallForwarding",
    "SQMConfig",
    "SQMQueue",
    # Mesh network info
    "Client",
    "MeshNode",
    "MeshNetwork",
    "collect_node_info",
    "collect_mesh_network",
    "display_mesh_tree",
    # Progress utilities
    "Spinner",
    "ProgressBar",
    "spinner",
    "progress_bar",
]
