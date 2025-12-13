"""Network configuration components."""

from typing import List
from .base import UCISection, BaseBuilder, UCICommand


class NetworkDevice(UCISection):
    """Represents a network device configuration."""

    def __init__(self, name: str):
        super().__init__("network", name, "device")


class NetworkInterface(UCISection):
    """Represents a network interface configuration."""

    def __init__(self, name: str):
        super().__init__("network", name, "interface")


class DeviceBuilder(BaseBuilder):
    """Builder for network devices."""

    def __init__(self, section: NetworkDevice):
        super().__init__(section)

    def name(self, value: str) -> "DeviceBuilder":
        """Set the device name."""
        return self._set("name", value)

    def type(self, value: str) -> "DeviceBuilder":
        """Set the device type (e.g., 'bridge', '8021q')."""
        return self._set("type", value)

    def add_port(self, port: str) -> "DeviceBuilder":
        """Add a port to the device."""
        return self._add_list("ports", port)

    def ifname(self, value: str) -> "DeviceBuilder":
        """Set the interface name."""
        return self._set("ifname", value)

    def vid(self, value: int) -> "DeviceBuilder":
        """Set the VLAN ID."""
        return self._set("vid", value)


class InterfaceBuilder(BaseBuilder):
    """Builder for network interfaces."""

    def __init__(self, section: NetworkInterface):
        super().__init__(section)

    def device(self, value: str) -> "InterfaceBuilder":
        """Set the device for this interface."""
        return self._set("device", value)

    def proto(self, value: str) -> "InterfaceBuilder":
        """Set the protocol (e.g., 'static', 'dhcp', 'batadv')."""
        return self._set("proto", value)

    def ipaddr(self, value: str) -> "InterfaceBuilder":
        """Set the IP address."""
        return self._set("ipaddr", value)

    def netmask(self, value: str) -> "InterfaceBuilder":
        """Set the netmask."""
        return self._set("netmask", value)

    def gateway(self, value: str) -> "InterfaceBuilder":
        """Set the gateway."""
        return self._set("gateway", value)

    def master(self, value: str) -> "InterfaceBuilder":
        """Set the master interface (for batman-adv)."""
        return self._set("master", value)

    def mtu(self, value: int) -> "InterfaceBuilder":
        """Set the MTU."""
        return self._set("mtu", value)

    def routing_algo(self, value: str) -> "InterfaceBuilder":
        """Set the routing algorithm (for batman-adv)."""
        return self._set("routing_algo", value)

    def gw_mode(self, value: str) -> "InterfaceBuilder":
        """Set the gateway mode (for batman-adv)."""
        return self._set("gw_mode", value)

    def gw_bandwidth(self, value: str) -> "InterfaceBuilder":
        """Set the gateway bandwidth (for batman-adv)."""
        return self._set("gw_bandwidth", value)

    def hop_penalty(self, value: int) -> "InterfaceBuilder":
        """Set the hop penalty (for batman-adv)."""
        return self._set("hop_penalty", value)

    def orig_interval(self, value: int) -> "InterfaceBuilder":
        """Set the originator interval (for batman-adv)."""
        return self._set("orig_interval", value)


class NetworkConfig:
    """Network configuration manager."""

    def __init__(self) -> None:
        self.devices: List[NetworkDevice] = []
        self.interfaces: List[NetworkInterface] = []

    def device(self, name: str) -> DeviceBuilder:
        """Create a new network device."""
        dev = NetworkDevice(name)
        self.devices.append(dev)
        return DeviceBuilder(dev)

    def interface(self, name: str) -> InterfaceBuilder:
        """Create a new network interface."""
        iface = NetworkInterface(name)
        self.interfaces.append(iface)
        return InterfaceBuilder(iface)

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for network configuration."""
        commands = []
        for device in self.devices:
            commands.extend(device.get_commands())
        for interface in self.interfaces:
            commands.extend(interface.get_commands())
        return commands
