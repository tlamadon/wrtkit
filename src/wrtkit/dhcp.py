"""DHCP configuration components."""

from typing import Any, List, Optional
from pydantic import Field, AliasChoices
from .base import UCISection, UCICommand, RemotePolicy


class DHCPHost(UCISection):
    """Represents a DHCP static lease (host) entry."""

    mac: Optional[str] = Field(None, validation_alias=AliasChoices("mac", "macaddr"))
    ip: Optional[str] = Field(None, validation_alias=AliasChoices("ip", "ipaddr"))
    name: Optional[str] = Field(None, validation_alias=AliasChoices("name", "hostname"))
    leasetime: Optional[str] = None

    def __init__(self, host_name: str, **data: Any) -> None:
        super().__init__(**data)
        self._package = "dhcp"
        self._section = host_name
        self._section_type = "host"

    # Immutable builder methods (composable)
    def with_mac(self, value: str) -> "DHCPHost":
        """Set the MAC address for this static lease (returns new copy)."""
        return self.model_copy(update={"mac": value})

    def with_ip(self, value: str) -> "DHCPHost":
        """Set the IP address for this static lease (returns new copy)."""
        return self.model_copy(update={"ip": value})

    def with_name(self, value: str) -> "DHCPHost":
        """Set the hostname for this static lease (returns new copy)."""
        return self.model_copy(update={"name": value})

    def with_leasetime(self, value: str) -> "DHCPHost":
        """Set the lease time for this static lease (returns new copy)."""
        return self.model_copy(update={"leasetime": value})

    # Convenience builder for common configuration
    def with_static_lease(self, mac: str, ip: str, name: Optional[str] = None) -> "DHCPHost":
        """Configure a complete static lease (returns new copy)."""
        updates = {"mac": mac, "ip": ip}
        if name is not None:
            updates["name"] = name
        return self.model_copy(update=updates)


class DHCPSection(UCISection):
    """Represents a DHCP configuration section."""

    interface: Optional[str] = None
    start: Optional[int] = None
    limit: Optional[int] = None
    leasetime: Optional[str] = None
    ignore: Optional[bool] = None

    def __init__(self, dhcp_name: str, **data: Any) -> None:
        super().__init__(**data)
        self._package = "dhcp"
        self._section = dhcp_name
        self._section_type = "dhcp"

    # Immutable builder methods (composable)
    def with_interface(self, value: str) -> "DHCPSection":
        """Set the interface for this DHCP server (returns new copy)."""
        return self.model_copy(update={"interface": value})

    def with_start(self, value: int) -> "DHCPSection":
        """Set the start of the IP address range (returns new copy)."""
        return self.model_copy(update={"start": value})

    def with_limit(self, value: int) -> "DHCPSection":
        """Set the number of addresses in the pool (returns new copy)."""
        return self.model_copy(update={"limit": value})

    def with_leasetime(self, value: str) -> "DHCPSection":
        """Set the lease time (e.g., '12h', '24h') (returns new copy)."""
        return self.model_copy(update={"leasetime": value})

    def with_ignore(self, value: bool) -> "DHCPSection":
        """Enable or disable this DHCP server (returns new copy)."""
        return self.model_copy(update={"ignore": value})

    # Convenience builder methods for common configurations
    def with_range(self, start: int, limit: int, leasetime: str = "12h") -> "DHCPSection":
        """Configure DHCP address range (returns new copy)."""
        return self.model_copy(update={"start": start, "limit": limit, "leasetime": leasetime})


class DHCPConfig(UCISection):
    """DHCP configuration manager."""

    sections: List[DHCPSection] = Field(default_factory=list)
    hosts: List[DHCPHost] = Field(default_factory=list)
    remote_policy: Optional[RemotePolicy] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._package = "dhcp"
        self._section = ""
        self._section_type = ""

    def add_dhcp(self, dhcp: DHCPSection) -> "DHCPConfig":
        """Add a DHCP section and return self for chaining."""
        self.sections.append(dhcp)
        return self

    def add_host(self, host: DHCPHost) -> "DHCPConfig":
        """Add a DHCP static lease (host) and return self for chaining."""
        self.hosts.append(host)
        return self

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for DHCP configuration."""
        commands = []
        for section in self.sections:
            commands.extend(section.get_commands())
        for host in self.hosts:
            commands.extend(host.get_commands())
        return commands
