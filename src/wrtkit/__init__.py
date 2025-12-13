"""WRTKit - A Python library for managing OpenWRT configuration over SSH."""

from .config import UCIConfig
from .ssh import SSHConnection
from .network import NetworkConfig, DeviceBuilder, InterfaceBuilder
from .wireless import WirelessConfig, RadioBuilder, WiFiInterfaceBuilder
from .dhcp import DHCPConfig, DHCPBuilder
from .firewall import FirewallConfig, ZoneBuilder, ForwardingBuilder

__version__ = "0.1.0"

__all__ = [
    "UCIConfig",
    "SSHConnection",
    "NetworkConfig",
    "DeviceBuilder",
    "InterfaceBuilder",
    "WirelessConfig",
    "RadioBuilder",
    "WiFiInterfaceBuilder",
    "DHCPConfig",
    "DHCPBuilder",
    "FirewallConfig",
    "ZoneBuilder",
    "ForwardingBuilder",
]
