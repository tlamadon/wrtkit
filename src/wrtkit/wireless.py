"""Wireless configuration components."""

from typing import Any, List, Optional
from pydantic import Field
from .base import UCISection, UCICommand


class WirelessRadio(UCISection):
    """Represents a wireless radio configuration."""

    channel: Optional[int] = None
    htmode: Optional[str] = None
    country: Optional[str] = None
    disabled: Optional[bool] = None
    txpower: Optional[int] = None

    def __init__(self, radio_name: str, **data: Any) -> None:
        super().__init__(**data)
        self._package = "wireless"
        self._section = radio_name
        self._section_type = "wifi-device"

    # Immutable builder methods (composable)
    def with_channel(self, value: int) -> "WirelessRadio":
        """Set the wireless channel (returns new copy)."""
        return self.model_copy(update={"channel": value})

    def with_htmode(self, value: str) -> "WirelessRadio":
        """Set the HT mode (e.g., 'HT20', 'HT40', 'VHT80') (returns new copy)."""
        return self.model_copy(update={"htmode": value})

    def with_country(self, value: str) -> "WirelessRadio":
        """Set the country code (returns new copy)."""
        return self.model_copy(update={"country": value})

    def with_disabled(self, value: bool) -> "WirelessRadio":
        """Enable or disable the radio (returns new copy)."""
        return self.model_copy(update={"disabled": value})

    def with_txpower(self, value: int) -> "WirelessRadio":
        """Set the transmission power (returns new copy)."""
        return self.model_copy(update={"txpower": value})


class WirelessInterface(UCISection):
    """Represents a wireless interface configuration."""

    device: Optional[str] = None
    mode: Optional[str] = None
    network: Optional[str] = None
    ssid: Optional[str] = None
    encryption: Optional[str] = None
    key: Optional[str] = None
    ifname: Optional[str] = None
    mesh_id: Optional[str] = None
    mesh_fwding: Optional[bool] = None
    mcast_rate: Optional[int] = None
    ieee80211r: Optional[bool] = None
    ft_over_ds: Optional[bool] = None
    ft_psk_generate_local: Optional[bool] = None

    def __init__(self, iface_name: str, **data: Any) -> None:
        super().__init__(**data)
        self._package = "wireless"
        self._section = iface_name
        self._section_type = "wifi-iface"

    # Immutable builder methods (composable)
    def with_device(self, value: str) -> "WirelessInterface":
        """Set the radio device for this interface (returns new copy)."""
        return self.model_copy(update={"device": value})

    def with_mode(self, value: str) -> "WirelessInterface":
        """Set the mode (e.g., 'ap', 'sta', 'mesh') (returns new copy)."""
        return self.model_copy(update={"mode": value})

    def with_network(self, value: str) -> "WirelessInterface":
        """Set the network this interface belongs to (returns new copy)."""
        return self.model_copy(update={"network": value})

    def with_ssid(self, value: str) -> "WirelessInterface":
        """Set the SSID (returns new copy)."""
        return self.model_copy(update={"ssid": value})

    def with_encryption(self, value: str) -> "WirelessInterface":
        """Set the encryption type (e.g., 'psk2', 'sae', 'none') (returns new copy)."""
        return self.model_copy(update={"encryption": value})

    def with_key(self, value: str) -> "WirelessInterface":
        """Set the encryption key/password (returns new copy)."""
        return self.model_copy(update={"key": value})

    def with_ifname(self, value: str) -> "WirelessInterface":
        """Set the interface name (returns new copy)."""
        return self.model_copy(update={"ifname": value})

    def with_mesh_id(self, value: str) -> "WirelessInterface":
        """Set the mesh ID (for mesh mode) (returns new copy)."""
        return self.model_copy(update={"mesh_id": value})

    def with_mesh_fwding(self, value: bool) -> "WirelessInterface":
        """Enable or disable mesh forwarding (returns new copy)."""
        return self.model_copy(update={"mesh_fwding": value})

    def with_mcast_rate(self, value: int) -> "WirelessInterface":
        """Set the multicast rate (returns new copy)."""
        return self.model_copy(update={"mcast_rate": value})

    def with_ieee80211r(self, value: bool) -> "WirelessInterface":
        """Enable or disable 802.11r fast transition (returns new copy)."""
        return self.model_copy(update={"ieee80211r": value})

    def with_ft_over_ds(self, value: bool) -> "WirelessInterface":
        """Enable or disable FT over DS (returns new copy)."""
        return self.model_copy(update={"ft_over_ds": value})

    def with_ft_psk_generate_local(self, value: bool) -> "WirelessInterface":
        """Enable or disable local PSK generation for FT (returns new copy)."""
        return self.model_copy(update={"ft_psk_generate_local": value})

    # Convenience builder methods for common configurations
    def with_ap(self, ssid: str, encryption: str = "psk2", key: Optional[str] = None) -> "WirelessInterface":
        """Configure as access point (returns new copy)."""
        updates = {"mode": "ap", "ssid": ssid, "encryption": encryption}
        if key:
            updates["key"] = key
        return self.model_copy(update=updates)

    def with_mesh(self, mesh_id: str, encryption: str = "sae", key: Optional[str] = None) -> "WirelessInterface":
        """Configure as mesh interface (returns new copy)."""
        updates = {"mode": "mesh", "mesh_id": mesh_id, "encryption": encryption}
        if key:
            updates["key"] = key
        return self.model_copy(update=updates)


class WirelessConfig(UCISection):
    """Wireless configuration manager."""

    radios: List[WirelessRadio] = Field(default_factory=list)
    interfaces: List[WirelessInterface] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._package = "wireless"
        self._section = ""
        self._section_type = ""

    def add_radio(self, radio: WirelessRadio) -> "WirelessConfig":
        """Add a radio and return self for chaining."""
        self.radios.append(radio)
        return self

    def add_interface(self, interface: WirelessInterface) -> "WirelessConfig":
        """Add an interface and return self for chaining."""
        self.interfaces.append(interface)
        return self

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for wireless configuration."""
        commands = []
        for radio in self.radios:
            commands.extend(radio.get_commands())
        for interface in self.interfaces:
            commands.extend(interface.get_commands())
        return commands
