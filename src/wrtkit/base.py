"""Base classes for UCI configuration components."""

import fnmatch
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound="UCISection")


class RemotePolicy(BaseModel):
    """
    Policy for handling remote-only sections and values.

    This defines which remote sections and values are allowed to exist
    without being scheduled for deletion. Anything not matching these
    patterns will be marked for removal when syncing.

    Attributes:
        allowed_sections: DEPRECATED - Use whitelist instead.
            List of allowed section name patterns.
            Use "*" to allow all sections, or specific patterns like
            "wan*", "guest", etc. Supports glob-style wildcards.
        allowed_values: DEPRECATED - Use whitelist instead.
            List of allowed value patterns for options.
            Use "*" to allow all values. Supports glob-style wildcards.
            When specified, only matching values will be preserved.
        whitelist: List of path glob patterns to preserve on remote.
            Each pattern can match paths at any level within a config section.
            Examples:
              - "devices.br_lan.ports" - keep all ports on br_lan device
              - "devices.*.lan" - keep 'lan' option on any device
              - "interfaces.guest.*" - keep everything under guest interface
              - "interfaces.*.gateway" - keep gateway on any interface
              - "**" - keep everything (matches any path)

            Path patterns are relative to the package level (network, wireless, etc).
            The package is determined by which config section contains the policy.
    """

    # Legacy fields for backward compatibility
    allowed_sections: List[str] = Field(default_factory=list)
    allowed_values: List[str] = Field(default_factory=list)

    # New whitelist-based approach
    whitelist: List[str] = Field(default_factory=list)

    def _match_path_pattern(self, path: str, pattern: str) -> bool:
        """
        Match a path against a glob pattern, supporting ** for multiple segments.

        Args:
            path: The path to check (e.g., "devices.br_lan.ports")
            pattern: The pattern to match against (e.g., "devices.*.ports" or "devices.**")

        Returns:
            True if the path matches the pattern
        """
        # Handle exact wildcard match
        if pattern == "**":
            return True

        # Split path and pattern into segments
        path_parts = path.split(".")
        pattern_parts = pattern.split(".")

        # Track positions in both lists
        p_idx = 0  # path index
        pat_idx = 0  # pattern index

        while p_idx < len(path_parts) and pat_idx < len(pattern_parts):
            pattern_segment = pattern_parts[pat_idx]

            if pattern_segment == "**":
                # ** can match zero or more segments
                # Try to match the rest of the pattern with remaining path
                if pat_idx == len(pattern_parts) - 1:
                    # ** is at the end, matches everything remaining
                    return True

                # Try to match remaining pattern at each position in remaining path
                for i in range(p_idx, len(path_parts) + 1):
                    remaining_path = ".".join(path_parts[i:])
                    remaining_pattern = ".".join(pattern_parts[pat_idx + 1:])
                    if self._match_path_pattern(remaining_path, remaining_pattern):
                        return True
                return False
            elif pattern_segment == "*":
                # * matches exactly one segment
                p_idx += 1
                pat_idx += 1
            elif fnmatch.fnmatch(path_parts[p_idx], pattern_segment):
                # Regular segment match with glob support
                p_idx += 1
                pat_idx += 1
            else:
                # No match
                return False

        # Both must be exhausted for a full match
        return p_idx == len(path_parts) and pat_idx == len(pattern_parts)

    def is_path_whitelisted(self, path: str) -> bool:
        """
        Check if a path matches any whitelist pattern.

        Special case: If a pattern ends with ".*", it also matches the path
        without the wildcard. For example, "interfaces.guest.*" matches both
        "interfaces.guest" and "interfaces.guest.proto".

        Args:
            path: The relative path to check (e.g., "devices.br_lan.ports")

        Returns:
            True if the path matches any whitelist pattern
        """
        if not self.whitelist:
            return False

        for pattern in self.whitelist:
            if self._match_path_pattern(path, pattern):
                return True

            # Special case: pattern ending with .* should also match without the .*
            # This ensures that "interfaces.guest.*" whitelists the section definition too
            if pattern.endswith(".*"):
                prefix = pattern[:-2]  # Remove the ".*"
                if path == prefix:
                    return True

        return False

    def is_section_allowed(self, section_name: str) -> bool:
        """
        Check if a section name is allowed by this policy.

        DEPRECATED: Use is_path_whitelisted instead with new whitelist approach.

        Args:
            section_name: The section name to check

        Returns:
            True if the section matches any allowed pattern, False otherwise.
            Returns False if allowed_sections is empty (nothing explicitly allowed).
        """
        if not self.allowed_sections:
            return False

        for pattern in self.allowed_sections:
            if pattern == "*":
                return True
            if fnmatch.fnmatch(section_name, pattern):
                return True
        return False

    def is_value_allowed(self, value: str) -> bool:
        """
        Check if a value is allowed by this policy.

        DEPRECATED: Use is_path_whitelisted instead with new whitelist approach.

        Args:
            value: The value to check

        Returns:
            True if the value matches any allowed pattern, False otherwise.
            Returns True if allowed_values is empty (no value filtering).
        """
        if not self.allowed_values:
            # No value filtering - all values allowed
            return True

        for pattern in self.allowed_values:
            if pattern == "*":
                return True
            if fnmatch.fnmatch(str(value), pattern):
                return True
        return False

    def should_keep_remote_section(self, section_name: str) -> bool:
        """
        Determine if a remote-only section should be kept.

        DEPRECATED: Use should_keep_remote_path instead with new whitelist approach.

        Args:
            section_name: The section name to check

        Returns:
            True if the section should be kept, False if it should be deleted.
        """
        return self.is_section_allowed(section_name)

    def should_keep_remote_value(self, section_name: str, value: str) -> bool:
        """
        Determine if a remote-only value should be kept.

        DEPRECATED: Use should_keep_remote_path instead with new whitelist approach.

        Args:
            section_name: The section name containing the value
            value: The value to check

        Returns:
            True if the value should be kept, False if it should be deleted.
        """
        # First check if the section is allowed
        if not self.is_section_allowed(section_name):
            return False
        # Then check if the value is allowed
        return self.is_value_allowed(value)

    def should_keep_remote_path(self, path: str) -> bool:
        """
        Determine if a remote path should be kept based on whitelist.

        This is the new primary method for checking remote paths.
        Falls back to legacy allowed_sections/allowed_values if whitelist is empty.

        Args:
            path: The relative path to check (e.g., "devices.br_lan" or "interfaces.lan.gateway")

        Returns:
            True if the path should be kept, False if it should be deleted.
        """
        # Use new whitelist approach if configured
        if self.whitelist:
            return self.is_path_whitelisted(path)

        # Fall back to legacy behavior for backward compatibility
        parts = path.split(".")
        if len(parts) >= 1:
            # For section-level paths (e.g., "devices.br_lan")
            # Check if the section type and name pattern match
            section_name = parts[1] if len(parts) >= 2 else parts[0]
            return self.is_section_allowed(section_name)

        return False


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
        elif self.action == "del_list":
            return f"uci del_list {self.path}='{self.value}'"
        elif self.action == "delete":
            return f"uci delete {self.path}"
        else:
            raise ValueError(f"Unknown action: {self.action}")

    def to_string_with_value(self, display_value: str) -> str:
        """Convert command to UCI string format with a custom display value.

        This is useful for masking sensitive values in output.

        Args:
            display_value: The value to display instead of the actual value
        """
        if self.action == "set":
            return f"uci set {self.path}='{display_value}'"
        elif self.action == "add_list":
            return f"uci add_list {self.path}='{display_value}'"
        elif self.action == "del_list":
            return f"uci del_list {self.path}='{display_value}'"
        elif self.action == "delete":
            return f"uci delete {self.path}"
        else:
            raise ValueError(f"Unknown action: {self.action}")

    def __repr__(self) -> str:
        return f"UCICommand({self.action}, {self.path}, {self.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UCICommand):
            return False
        return self.action == other.action and self.path == other.path and self.value == other.value


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
        commands.append(UCICommand("set", f"{self._package}.{self._section}", self._section_type))

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
                            self._get_option_value(item),
                        )
                    )
            else:
                # Handle single-value options
                commands.append(
                    UCICommand(
                        "set",
                        f"{self._package}.{self._section}.{field_name}",
                        self._get_option_value(field_value),
                    )
                )

        return commands

    # Schema generation methods
    @classmethod
    def json_schema(cls, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate JSON Schema for this model.

        Args:
            title: Optional title for the schema

        Returns:
            JSON Schema as a dictionary
        """
        schema = cls.model_json_schema()
        if title:
            schema["title"] = title
        return schema

    @classmethod
    def yaml_schema(cls, title: Optional[str] = None) -> str:
        """
        Generate YAML Schema for this model.

        Returns JSON Schema in YAML format for better readability.

        Args:
            title: Optional title for the schema

        Returns:
            JSON Schema in YAML format as a string
        """
        import yaml

        schema = cls.json_schema(title)
        return yaml.dump(schema, default_flow_style=False, sort_keys=False)

    # Serialization methods
    def to_dict(self, exclude_none: bool = True, exclude_private: bool = True) -> Dict[str, Any]:
        """
        Convert this model to a dictionary.

        Args:
            exclude_none: Whether to exclude None values
            exclude_private: Whether to exclude fields starting with _

        Returns:
            Dictionary representation
        """
        data = self.model_dump(exclude_none=exclude_none)
        if exclude_private:
            data = {k: v for k, v in data.items() if not k.startswith("_")}
        return data

    def to_json(
        self, exclude_none: bool = True, exclude_private: bool = True, indent: int = 2
    ) -> str:
        """
        Convert this model to JSON string.

        Args:
            exclude_none: Whether to exclude None values
            exclude_private: Whether to exclude fields starting with _
            indent: Indentation level for pretty printing

        Returns:
            JSON string representation
        """
        import json

        data = self.to_dict(exclude_none, exclude_private)
        return json.dumps(data, indent=indent)

    def to_yaml(self, exclude_none: bool = True, exclude_private: bool = True) -> str:
        """
        Convert this model to YAML string.

        Args:
            exclude_none: Whether to exclude None values
            exclude_private: Whether to exclude fields starting with _

        Returns:
            YAML string representation
        """
        import yaml

        data = self.to_dict(exclude_none, exclude_private)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    # Deserialization methods
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any], section_name: str) -> T:
        """
        Create an instance from a dictionary.

        Args:
            data: Dictionary containing the model data
            section_name: Section name for this UCI section

        Returns:
            Instance of this model
        """
        return cls(section_name, **data)  # type: ignore[misc]

    @classmethod
    def from_json(cls: Type[T], json_str: str, section_name: str) -> T:
        """
        Create an instance from JSON string.

        Args:
            json_str: JSON string
            section_name: Section name for this UCI section

        Returns:
            Instance of this model
        """
        import json

        data = json.loads(json_str)
        return cls.from_dict(data, section_name)

    @classmethod
    def from_yaml(cls: Type[T], yaml_str: str, section_name: str) -> T:
        """
        Create an instance from YAML string.

        Args:
            yaml_str: YAML string
            section_name: Section name for this UCI section

        Returns:
            Instance of this model
        """
        import yaml

        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data, section_name)

    @classmethod
    def from_json_file(cls: Type[T], filename: str, section_name: str) -> T:
        """
        Create an instance from JSON file.

        Args:
            filename: Path to JSON file
            section_name: Section name for this UCI section

        Returns:
            Instance of this model
        """
        with open(filename, "r") as f:
            return cls.from_json(f.read(), section_name)

    @classmethod
    def from_yaml_file(cls: Type[T], filename: str, section_name: str) -> T:
        """
        Create an instance from YAML file.

        Args:
            filename: Path to YAML file
            section_name: Section name for this UCI section

        Returns:
            Instance of this model
        """
        with open(filename, "r") as f:
            return cls.from_yaml(f.read(), section_name)

    def to_json_file(
        self,
        filename: str,
        exclude_none: bool = True,
        exclude_private: bool = True,
        indent: int = 2,
    ) -> None:
        """
        Save this model to JSON file.

        Args:
            filename: Path to output file
            exclude_none: Whether to exclude None values
            exclude_private: Whether to exclude fields starting with _
            indent: Indentation level for pretty printing
        """
        json_str = self.to_json(exclude_none, exclude_private, indent)
        with open(filename, "w") as f:
            f.write(json_str)

    def to_yaml_file(
        self, filename: str, exclude_none: bool = True, exclude_private: bool = True
    ) -> None:
        """
        Save this model to YAML file.

        Args:
            filename: Path to output file
            exclude_none: Whether to exclude None values
            exclude_private: Whether to exclude fields starting with _
        """
        yaml_str = self.to_yaml(exclude_none, exclude_private)
        with open(filename, "w") as f:
            f.write(yaml_str)
