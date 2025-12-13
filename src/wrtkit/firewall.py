"""Firewall configuration components."""

from typing import List
from .base import UCISection, BaseBuilder, UCICommand


class FirewallZone(UCISection):
    """Represents a firewall zone configuration."""

    def __init__(self, index: int):
        super().__init__("firewall", f"@zone[{index}]", "zone")
        self.index = index


class FirewallForwarding(UCISection):
    """Represents a firewall forwarding rule."""

    def __init__(self, index: int):
        super().__init__("firewall", f"@forwarding[{index}]", "forwarding")
        self.index = index


class ZoneBuilder(BaseBuilder):
    """Builder for firewall zones."""

    def __init__(self, section: FirewallZone):
        super().__init__(section)

    def name(self, value: str) -> "ZoneBuilder":
        """Set the zone name."""
        return self._set("name", value)

    def input(self, value: str) -> "ZoneBuilder":
        """Set the input policy (ACCEPT, REJECT, DROP)."""
        return self._set("input", value)

    def output(self, value: str) -> "ZoneBuilder":
        """Set the output policy (ACCEPT, REJECT, DROP)."""
        return self._set("output", value)

    def forward(self, value: str) -> "ZoneBuilder":
        """Set the forward policy (ACCEPT, REJECT, DROP)."""
        return self._set("forward", value)

    def masq(self, value: bool) -> "ZoneBuilder":
        """Enable or disable masquerading."""
        return self._set("masq", value)

    def mtu_fix(self, value: bool) -> "ZoneBuilder":
        """Enable or disable MTU fix."""
        return self._set("mtu_fix", value)

    def add_network(self, network: str) -> "ZoneBuilder":
        """Add a network to this zone."""
        return self._add_list("network", network)


class ForwardingBuilder(BaseBuilder):
    """Builder for firewall forwarding rules."""

    def __init__(self, section: FirewallForwarding):
        super().__init__(section)

    def src(self, value: str) -> "ForwardingBuilder":
        """Set the source zone."""
        return self._set("src", value)

    def dest(self, value: str) -> "ForwardingBuilder":
        """Set the destination zone."""
        return self._set("dest", value)


class FirewallConfig:
    """Firewall configuration manager."""

    def __init__(self) -> None:
        self.zones: List[FirewallZone] = []
        self.forwardings: List[FirewallForwarding] = []

    def zone(self, index: int) -> ZoneBuilder:
        """Configure a firewall zone at the specified index."""
        zone = FirewallZone(index)
        self.zones.append(zone)
        return ZoneBuilder(zone)

    def forwarding(self, index: int) -> ForwardingBuilder:
        """Create a firewall forwarding rule at the specified index."""
        forwarding = FirewallForwarding(index)
        self.forwardings.append(forwarding)
        return ForwardingBuilder(forwarding)

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for firewall configuration."""
        commands = []
        for zone in self.zones:
            commands.extend(zone.get_commands())
        for forwarding in self.forwardings:
            commands.extend(forwarding.get_commands())
        return commands
