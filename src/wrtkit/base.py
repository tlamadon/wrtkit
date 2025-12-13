"""Base classes for UCI configuration components."""

from typing import Any, Dict, List, Optional, Union


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


class UCISection:
    """Base class for UCI configuration sections."""

    def __init__(self, package: str, section: str, section_type: str):
        self.package = package
        self.section = section
        self.section_type = section_type
        self.options: Dict[str, Union[str, List[str]]] = {}

    def set_option(self, key: str, value: Union[str, int, bool]) -> None:
        """Set a single-value option."""
        if isinstance(value, bool):
            value = "1" if value else "0"
        elif isinstance(value, int):
            value = str(value)
        self.options[key] = value

    def add_list_option(self, key: str, value: str) -> None:
        """Add a value to a list option."""
        if key not in self.options:
            self.options[key] = []
        if isinstance(self.options[key], list):
            self.options[key].append(value)
        else:
            raise ValueError(f"Option {key} is not a list")

    def get_commands(self) -> List[UCICommand]:
        """Generate UCI commands for this section."""
        commands = []

        # Set section type
        commands.append(
            UCICommand("set", f"{self.package}.{self.section}", self.section_type)
        )

        # Set all options
        for key, value in self.options.items():
            if isinstance(value, list):
                for item in value:
                    commands.append(
                        UCICommand("add_list", f"{self.package}.{self.section}.{key}", item)
                    )
            else:
                commands.append(
                    UCICommand("set", f"{self.package}.{self.section}.{key}", value)
                )

        return commands


class BaseBuilder:
    """Base class for builder pattern implementations."""

    def __init__(self, section: UCISection):
        self._section = section

    def _set(self, key: str, value: Union[str, int, bool]) -> "BaseBuilder":
        """Set an option and return self for chaining."""
        self._section.set_option(key, value)
        return self

    def _add_list(self, key: str, value: str) -> "BaseBuilder":
        """Add to a list option and return self for chaining."""
        self._section.add_list_option(key, value)
        return self
