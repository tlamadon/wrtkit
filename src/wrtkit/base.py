"""Base classes for UCI configuration components."""

from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar('T', bound='UCISection')


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
            schema['title'] = title
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
            data = {k: v for k, v in data.items() if not k.startswith('_')}
        return data

    def to_json(self, exclude_none: bool = True, exclude_private: bool = True, indent: int = 2) -> str:
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
        with open(filename, 'r') as f:
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
        with open(filename, 'r') as f:
            return cls.from_yaml(f.read(), section_name)

    def to_json_file(self, filename: str, exclude_none: bool = True, exclude_private: bool = True, indent: int = 2) -> None:
        """
        Save this model to JSON file.

        Args:
            filename: Path to output file
            exclude_none: Whether to exclude None values
            exclude_private: Whether to exclude fields starting with _
            indent: Indentation level for pretty printing
        """
        json_str = self.to_json(exclude_none, exclude_private, indent)
        with open(filename, 'w') as f:
            f.write(json_str)

    def to_yaml_file(self, filename: str, exclude_none: bool = True, exclude_private: bool = True) -> None:
        """
        Save this model to YAML file.

        Args:
            filename: Path to output file
            exclude_none: Whether to exclude None values
            exclude_private: Whether to exclude fields starting with _
        """
        yaml_str = self.to_yaml(exclude_none, exclude_private)
        with open(filename, 'w') as f:
            f.write(yaml_str)
