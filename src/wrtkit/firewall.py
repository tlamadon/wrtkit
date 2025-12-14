"""Firewall configuration components."""

from typing import Any, List, Optional
from pydantic import Field
from .base import UCISection, UCICommand


class FirewallZone(UCISection):
    """Represents a firewall zone configuration."""

    name: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    forward: Optional[str] = None
    masq: Optional[bool] = None
    mtu_fix: Optional[bool] = None
    network: List[str] = Field(default_factory=list)

    def __init__(self, index: int, **data: Any) -> None:
        super().__init__(**data)
        self._package = "firewall"
        self._section = f"@zone[{index}]"
        self._section_type = "zone"
        self.index = index

    # Immutable builder methods (composable)
    def with_name(self, value: str) -> "FirewallZone":
        """Set the zone name (returns new copy)."""
        return self.model_copy(update={"name": value})

    def with_input(self, value: str) -> "FirewallZone":
        """Set the input policy (ACCEPT, REJECT, DROP) (returns new copy)."""
        return self.model_copy(update={"input": value})

    def with_output(self, value: str) -> "FirewallZone":
        """Set the output policy (ACCEPT, REJECT, DROP) (returns new copy)."""
        return self.model_copy(update={"output": value})

    def with_forward(self, value: str) -> "FirewallZone":
        """Set the forward policy (ACCEPT, REJECT, DROP) (returns new copy)."""
        return self.model_copy(update={"forward": value})

    def with_masq(self, value: bool) -> "FirewallZone":
        """Enable or disable masquerading (returns new copy)."""
        return self.model_copy(update={"masq": value})

    def with_mtu_fix(self, value: bool) -> "FirewallZone":
        """Enable or disable MTU fix (returns new copy)."""
        return self.model_copy(update={"mtu_fix": value})

    def with_network(self, network_name: str) -> "FirewallZone":
        """Add a network to this zone (returns new copy)."""
        networks = self.network.copy()
        networks.append(network_name)
        return self.model_copy(update={"network": networks})

    def with_networks(self, networks: List[str]) -> "FirewallZone":
        """Set all networks for this zone (returns new copy)."""
        return self.model_copy(update={"network": networks.copy()})

    # Convenience builder methods for common configurations
    def with_default_policies(self, input_policy: str = "ACCEPT", output_policy: str = "ACCEPT", forward_policy: str = "ACCEPT") -> "FirewallZone":
        """Set default policies for the zone (returns new copy)."""
        return self.model_copy(update={"input": input_policy, "output": output_policy, "forward": forward_policy})


class FirewallForwarding(UCISection):
    """Represents a firewall forwarding rule."""

    src: Optional[str] = None
    dest: Optional[str] = None

    def __init__(self, index: int, **data: Any) -> None:
        super().__init__(**data)
        self._package = "firewall"
        self._section = f"@forwarding[{index}]"
        self._section_type = "forwarding"
        self.index = index

    # Immutable builder methods (composable)
    def with_src(self, value: str) -> "FirewallForwarding":
        """Set the source zone (returns new copy)."""
        return self.model_copy(update={"src": value})

    def with_dest(self, value: str) -> "FirewallForwarding":
        """Set the destination zone (returns new copy)."""
        return self.model_copy(update={"dest": value})


class FirewallConfig(UCISection):
    """Firewall configuration manager."""

    zones: List[FirewallZone] = Field(default_factory=list)
    forwardings: List[FirewallForwarding] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._package = "firewall"
        self._section = ""
        self._section_type = ""

    def add_zone(self, zone: FirewallZone) -> "FirewallConfig":
        """Add a zone and return self for chaining."""
        self.zones.append(zone)
        return self

    def add_forwarding(self, forwarding: FirewallForwarding) -> "FirewallConfig":
        """Add a forwarding rule and return self for chaining."""
        self.forwardings.append(forwarding)
        return self

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for firewall configuration."""
        commands = []
        for zone in self.zones:
            commands.extend(zone.get_commands())
        for forwarding in self.forwardings:
            commands.extend(forwarding.get_commands())
        return commands
