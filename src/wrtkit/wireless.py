"""Wireless configuration components."""

from typing import List
from .base import UCISection, BaseBuilder, UCICommand


class WirelessRadio(UCISection):
    """Represents a wireless radio configuration."""

    def __init__(self, name: str):
        super().__init__("wireless", name, "wifi-device")


class WirelessInterface(UCISection):
    """Represents a wireless interface configuration."""

    def __init__(self, name: str):
        super().__init__("wireless", name, "wifi-iface")


class RadioBuilder(BaseBuilder):
    """Builder for wireless radios."""

    def __init__(self, section: WirelessRadio):
        super().__init__(section)

    def channel(self, value: int) -> "RadioBuilder":
        """Set the wireless channel."""
        return self._set("channel", value)

    def htmode(self, value: str) -> "RadioBuilder":
        """Set the HT mode (e.g., 'HT20', 'HT40', 'VHT80')."""
        return self._set("htmode", value)

    def country(self, value: str) -> "RadioBuilder":
        """Set the country code."""
        return self._set("country", value)

    def disabled(self, value: bool) -> "RadioBuilder":
        """Enable or disable the radio."""
        return self._set("disabled", value)

    def txpower(self, value: int) -> "RadioBuilder":
        """Set the transmission power."""
        return self._set("txpower", value)


class WiFiInterfaceBuilder(BaseBuilder):
    """Builder for wireless interfaces."""

    def __init__(self, section: WirelessInterface):
        super().__init__(section)

    def device(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the radio device for this interface."""
        return self._set("device", value)

    def mode(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the mode (e.g., 'ap', 'sta', 'mesh')."""
        return self._set("mode", value)

    def network(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the network this interface belongs to."""
        return self._set("network", value)

    def ssid(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the SSID."""
        return self._set("ssid", value)

    def encryption(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the encryption type (e.g., 'psk2', 'sae', 'none')."""
        return self._set("encryption", value)

    def key(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the encryption key/password."""
        return self._set("key", value)

    def ifname(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the interface name."""
        return self._set("ifname", value)

    def mesh_id(self, value: str) -> "WiFiInterfaceBuilder":
        """Set the mesh ID (for mesh mode)."""
        return self._set("mesh_id", value)

    def mesh_fwding(self, value: bool) -> "WiFiInterfaceBuilder":
        """Enable or disable mesh forwarding."""
        return self._set("mesh_fwding", value)

    def mcast_rate(self, value: int) -> "WiFiInterfaceBuilder":
        """Set the multicast rate."""
        return self._set("mcast_rate", value)

    def ieee80211r(self, value: bool) -> "WiFiInterfaceBuilder":
        """Enable or disable 802.11r fast transition."""
        return self._set("ieee80211r", value)

    def ft_over_ds(self, value: bool) -> "WiFiInterfaceBuilder":
        """Enable or disable FT over DS."""
        return self._set("ft_over_ds", value)

    def ft_psk_generate_local(self, value: bool) -> "WiFiInterfaceBuilder":
        """Enable or disable local PSK generation for FT."""
        return self._set("ft_psk_generate_local", value)


class WirelessConfig:
    """Wireless configuration manager."""

    def __init__(self) -> None:
        self.radios: List[WirelessRadio] = []
        self.interfaces: List[WirelessInterface] = []

    def radio(self, name: str) -> RadioBuilder:
        """Configure a wireless radio."""
        radio = WirelessRadio(name)
        self.radios.append(radio)
        return RadioBuilder(radio)

    def wifi_iface(self, name: str) -> WiFiInterfaceBuilder:
        """Create a new wireless interface."""
        iface = WirelessInterface(name)
        self.interfaces.append(iface)
        return WiFiInterfaceBuilder(iface)

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for wireless configuration."""
        commands = []
        for radio in self.radios:
            commands.extend(radio.get_commands())
        for interface in self.interfaces:
            commands.extend(interface.get_commands())
        return commands
