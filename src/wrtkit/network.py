"""Network configuration components."""

from typing import List, Optional
from pydantic import Field
from .base import UCISection, UCICommand


class NetworkDevice(UCISection):
    """Represents a network device configuration."""

    name: Optional[str] = None
    type: Optional[str] = None
    ports: List[str] = Field(default_factory=list)
    ifname: Optional[str] = None
    vid: Optional[int] = None

    def __init__(self, device_name: str, **data):
        super().__init__(**data)
        self._package = "network"
        self._section = device_name
        self._section_type = "device"

    # Immutable builder methods (composable)
    def with_name(self, value: str) -> "NetworkDevice":
        """Set the device name (returns new copy)."""
        return self.model_copy(update={"name": value})

    def with_type(self, value: str) -> "NetworkDevice":
        """Set the device type (e.g., 'bridge', '8021q') (returns new copy)."""
        return self.model_copy(update={"type": value})

    def with_port(self, port: str) -> "NetworkDevice":
        """Add a port to the device (returns new copy)."""
        ports = self.ports.copy()
        ports.append(port)
        return self.model_copy(update={"ports": ports})

    def with_ports(self, ports: List[str]) -> "NetworkDevice":
        """Set all ports for the device (returns new copy)."""
        return self.model_copy(update={"ports": ports.copy()})

    def with_ifname(self, value: str) -> "NetworkDevice":
        """Set the interface name (returns new copy)."""
        return self.model_copy(update={"ifname": value})

    def with_vid(self, value: int) -> "NetworkDevice":
        """Set the VLAN ID (returns new copy)."""
        return self.model_copy(update={"vid": value})


class NetworkInterface(UCISection):
    """Represents a network interface configuration."""

    device: Optional[str] = None
    proto: Optional[str] = None
    ipaddr: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    master: Optional[str] = None
    mtu: Optional[int] = None
    routing_algo: Optional[str] = None
    gw_mode: Optional[str] = None
    gw_bandwidth: Optional[str] = None
    hop_penalty: Optional[int] = None
    orig_interval: Optional[int] = None

    def __init__(self, interface_name: str, **data):
        super().__init__(**data)
        self._package = "network"
        self._section = interface_name
        self._section_type = "interface"

    # Immutable builder methods (composable)
    def with_device(self, value: str) -> "NetworkInterface":
        """Set the device for this interface (returns new copy)."""
        return self.model_copy(update={"device": value})

    def with_proto(self, value: str) -> "NetworkInterface":
        """Set the protocol (e.g., 'static', 'dhcp', 'batadv') (returns new copy)."""
        return self.model_copy(update={"proto": value})

    def with_ipaddr(self, value: str) -> "NetworkInterface":
        """Set the IP address (returns new copy)."""
        return self.model_copy(update={"ipaddr": value})

    def with_netmask(self, value: str) -> "NetworkInterface":
        """Set the netmask (returns new copy)."""
        return self.model_copy(update={"netmask": value})

    def with_gateway(self, value: str) -> "NetworkInterface":
        """Set the gateway (returns new copy)."""
        return self.model_copy(update={"gateway": value})

    def with_master(self, value: str) -> "NetworkInterface":
        """Set the master interface (for batman-adv) (returns new copy)."""
        return self.model_copy(update={"master": value})

    def with_mtu(self, value: int) -> "NetworkInterface":
        """Set the MTU (returns new copy)."""
        return self.model_copy(update={"mtu": value})

    def with_routing_algo(self, value: str) -> "NetworkInterface":
        """Set the routing algorithm (for batman-adv) (returns new copy)."""
        return self.model_copy(update={"routing_algo": value})

    def with_gw_mode(self, value: str) -> "NetworkInterface":
        """Set the gateway mode (for batman-adv) (returns new copy)."""
        return self.model_copy(update={"gw_mode": value})

    def with_gw_bandwidth(self, value: str) -> "NetworkInterface":
        """Set the gateway bandwidth (for batman-adv) (returns new copy)."""
        return self.model_copy(update={"gw_bandwidth": value})

    def with_hop_penalty(self, value: int) -> "NetworkInterface":
        """Set the hop penalty (for batman-adv) (returns new copy)."""
        return self.model_copy(update={"hop_penalty": value})

    def with_orig_interval(self, value: int) -> "NetworkInterface":
        """Set the originator interval (for batman-adv) (returns new copy)."""
        return self.model_copy(update={"orig_interval": value})

    # Convenience builder methods for common configurations
    def with_static_ip(self, ip: str, netmask: str = "255.255.255.0", gateway: Optional[str] = None) -> "NetworkInterface":
        """Configure interface with static IP (returns new copy)."""
        updates = {"proto": "static", "ipaddr": ip, "netmask": netmask}
        if gateway:
            updates["gateway"] = gateway
        return self.model_copy(update=updates)

    def with_dhcp(self) -> "NetworkInterface":
        """Configure interface to use DHCP (returns new copy)."""
        return self.model_copy(update={"proto": "dhcp"})


class NetworkConfig(UCISection):
    """Network configuration manager."""

    devices: List[NetworkDevice] = Field(default_factory=list)
    interfaces: List[NetworkInterface] = Field(default_factory=list)

    def __init__(self, **data):
        super().__init__(**data)
        self._package = "network"
        self._section = ""
        self._section_type = ""

    def add_device(self, device: NetworkDevice) -> "NetworkConfig":
        """Add a device and return self for chaining."""
        self.devices.append(device)
        return self

    def add_interface(self, interface: NetworkInterface) -> "NetworkConfig":
        """Add an interface and return self for chaining."""
        self.interfaces.append(interface)
        return self

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for network configuration."""
        commands = []
        for device in self.devices:
            commands.extend(device.get_commands())
        for interface in self.interfaces:
            commands.extend(interface.get_commands())
        return commands
