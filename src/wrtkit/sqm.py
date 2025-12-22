"""SQM (Smart Queue Management) configuration components."""

from typing import Any, List, Optional
from pydantic import Field
from .base import UCISection, UCICommand


class SQMQueue(UCISection):
    """Represents an SQM queue configuration section."""

    enabled: Optional[bool] = None
    interface: Optional[str] = None
    download: Optional[int] = None  # Download speed in Kbit/s
    upload: Optional[int] = None  # Upload speed in Kbit/s
    qdisc: Optional[str] = None  # Queue discipline (fq_codel, cake, etc.)
    script: Optional[str] = None  # SQM script (simple.qos, piece_of_cake.qos, etc.)
    qdisc_advanced: Optional[bool] = None
    ingress_ecn: Optional[str] = None  # ECN for ingress (ECN, NOECN)
    egress_ecn: Optional[str] = None  # ECN for egress (ECN, NOECN)
    qdisc_really_really_advanced: Optional[bool] = None
    itarget: Optional[str] = None  # Target interval for ingress
    etarget: Optional[str] = None  # Target interval for egress
    linklayer: Optional[str] = None  # Link layer adaptation (none, ethernet, atm)
    overhead: Optional[int] = None  # Per-packet overhead in bytes
    linklayer_advanced: Optional[bool] = None
    tcMTU: Optional[int] = None  # Maximum packet size
    tcTSIZE: Optional[int] = None  # Rate table size
    tcMPU: Optional[int] = None  # Minimum packet unit
    linklayer_adaptation_mechanism: Optional[str] = None  # tc_stab or cake
    iqdisc_opts: Optional[str] = None  # Extra ingress qdisc options
    eqdisc_opts: Optional[str] = None  # Extra egress qdisc options
    squash_dscp: Optional[str] = None  # Squash DSCP marks (1 or 0)
    squash_ingress: Optional[str] = None  # Squash ingress DSCP (1 or 0)

    def __init__(self, queue_name: str, **data: Any) -> None:
        super().__init__(**data)
        self._package = "sqm"
        self._section = queue_name
        self._section_type = "queue"

    # Immutable builder methods (composable)
    def with_enabled(self, value: bool) -> "SQMQueue":
        """Enable or disable this SQM queue (returns new copy)."""
        return self.model_copy(update={"enabled": value})

    def with_interface(self, value: str) -> "SQMQueue":
        """Set the interface for this SQM queue (returns new copy)."""
        return self.model_copy(update={"interface": value})

    def with_download(self, value: int) -> "SQMQueue":
        """Set the download speed in Kbit/s (returns new copy)."""
        return self.model_copy(update={"download": value})

    def with_upload(self, value: int) -> "SQMQueue":
        """Set the upload speed in Kbit/s (returns new copy)."""
        return self.model_copy(update={"upload": value})

    def with_qdisc(self, value: str) -> "SQMQueue":
        """Set the queue discipline (returns new copy)."""
        return self.model_copy(update={"qdisc": value})

    def with_script(self, value: str) -> "SQMQueue":
        """Set the SQM script (returns new copy)."""
        return self.model_copy(update={"script": value})

    def with_overhead(self, value: int) -> "SQMQueue":
        """Set the per-packet overhead in bytes (returns new copy)."""
        return self.model_copy(update={"overhead": value})

    def with_linklayer(self, value: str) -> "SQMQueue":
        """Set the link layer adaptation (returns new copy)."""
        return self.model_copy(update={"linklayer": value})

    def with_ingress_ecn(self, value: str) -> "SQMQueue":
        """Set the ingress ECN setting (returns new copy)."""
        return self.model_copy(update={"ingress_ecn": value})

    def with_egress_ecn(self, value: str) -> "SQMQueue":
        """Set the egress ECN setting (returns new copy)."""
        return self.model_copy(update={"egress_ecn": value})

    # Convenience builder methods for common configurations
    def with_speeds(self, download: int, upload: int) -> "SQMQueue":
        """Configure download and upload speeds in Kbit/s (returns new copy)."""
        return self.model_copy(update={"download": download, "upload": upload})

    def with_cake(self, download: int, upload: int) -> "SQMQueue":
        """Configure with CAKE qdisc (returns new copy)."""
        return self.model_copy(update={
            "qdisc": "cake",
            "script": "piece_of_cake.qos",
            "download": download,
            "upload": upload
        })

    def with_fq_codel(self, download: int, upload: int) -> "SQMQueue":
        """Configure with fq_codel qdisc (returns new copy)."""
        return self.model_copy(update={
            "qdisc": "fq_codel",
            "script": "simple.qos",
            "download": download,
            "upload": upload
        })

    def with_link_layer(self, linklayer: str, overhead: int) -> "SQMQueue":
        """Configure link layer adaptation (returns new copy)."""
        return self.model_copy(update={"linklayer": linklayer, "overhead": overhead})


class SQMConfig(UCISection):
    """SQM configuration manager."""

    queues: List[SQMQueue] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._package = "sqm"
        self._section = ""
        self._section_type = ""

    def add_queue(self, queue: SQMQueue) -> "SQMConfig":
        """Add an SQM queue and return self for chaining."""
        self.queues.append(queue)
        return self

    def get_commands(self) -> List[UCICommand]:
        """Get all UCI commands for SQM configuration."""
        commands = []
        for queue in self.queues:
            commands.extend(queue.get_commands())
        return commands
