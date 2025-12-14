"""Base classes for UCI configuration components."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class UCICommand:
    """Represents a single UCI command."""

    def __init__(self, action: str, path: str, value: Optional[str] = None):
        self.action = action
        self.path = path
        self.value = value

    def to_string(self) -> str:
        """Convert command to UCI string format."""
        if self.action == "set":
            return f"uci set {self.path}='{self.value}'"
        elif self.action == "add_list":
            return f"uci add_list {self.path}='{self.value}'"
        elif self.action == "delete":
            return f"uci delete {self.path}"
        else:
            raise ValueError(f"Unknown action: {self.action}")

    def __repr__(self) -> str:
        return f"UCICommand({self.action}, {self.path}, {self.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UCICommand):
            return False
        return (
            self.action == other.action
            and self.path == other.path
            and self.value == other.value
        )


class UCISection(BaseModel):
    """Base class for UCI configuration sections using Pydantic."""

    model_config = ConfigDict(extra="allow", validate_assignment=True)

    # Core UCI metadata
    _package: str = ""
    _section: str = ""
    _section_type: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Initialize UCI metadata after model creation."""
        # Subclasses should set these in their __init__
        pass

    def _get_option_value(self, value: Any) -> str:
        """Convert Python values to UCI string values."""
        if isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, int):
            return str(value)
        else:
            return str(value)

    def get_commands(self) -> List[UCICommand]:
        """Generate UCI commands for this section."""
        commands = []

        # Set section type
        commands.append(
            UCICommand("set", f"{self._package}.{self._section}", self._section_type)
        )

        # Get all fields except private ones (starting with _)
        for field_name, field_value in self.model_dump(exclude_none=True).items():
            if field_name.startswith("_"):
                continue

            if isinstance(field_value, list):
                # Handle list options
                for item in field_value:
                    commands.append(
                        UCICommand(
                            "add_list",
                            f"{self._package}.{self._section}.{field_name}",
                            self._get_option_value(item)
                        )
                    )
            else:
                # Handle single-value options
                commands.append(
                    UCICommand(
                        "set",
                        f"{self._package}.{self._section}.{field_name}",
                        self._get_option_value(field_value)
                    )
                )

        return commands
