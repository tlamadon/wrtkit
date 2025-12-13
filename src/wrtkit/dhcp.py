"""DHCP configuration components."""

from typing import List
from .base import UCISection, BaseBuilder, UCICommand


class DHCPSection(UCISection):
    """Represents a DHCP configuration section."""

    def __init__(self, name: str):
        super().__init__("dhcp", name, "dhcp")


class DHCPBuilder(BaseBuilder):
    """Builder for DHCP configurations."""

    def __init__(self, section: DHCPSection):
        super().__init__(section)

    def interface(self, value: str) -> "DHCPBuilder":
        """Set the interface for this DHCP server."""
        return self._set("interface", value)

    def start(self, value: int) -> "DHCPBuilder":
        """Set the start of the IP address range."""
        return self._set("start", value)

    def limit(self, value: int) -> "DHCPBuilder":
        """Set the number of addresses in the pool."""
        return self._set("limit", value)

    def leasetime(self, value: str) -> "DHCPBuilder":
        """Set the lease time (e.g., '12h', '24h')."""
        return self._set("leasetime", value)

    def ignore(self, value: bool) -> "DHCPBuilder":
        """Enable or disable this DHCP server."""
        return self._set("ignore", value)


class DHCPConfig:
    """DHCP configuration manager."""

    def __init__(self) -> None:
        self.sections: List[DHCPSection] = []

    def dhcp(self, name: str) -> DHCPBuilder:
        """Create a new DHCP server configuration."""
        section = DHCPSection(name)
        self.sections.append(section)
        return DHCPBuilder(section)

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for DHCP configuration."""
        commands = []
        for section in self.sections:
            commands.extend(section.get_commands())
        return commands
