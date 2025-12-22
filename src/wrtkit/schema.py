"""Schema generation and serialization utilities for UCI configuration."""

import json
import yaml
from omegaconf import OmegaConf
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def generate_json_schema(model: Type[BaseModel], title: str = None) -> Dict[str, Any]:
    """
    Generate JSON Schema for a Pydantic model.

    Args:
        model: The Pydantic model class
        title: Optional title for the schema

    Returns:
        JSON Schema as a dictionary
    """
    schema = model.model_json_schema()
    if title:
        schema['title'] = title
    return schema


def generate_yaml_schema(model: Type[BaseModel], title: str = None) -> str:
    """
    Generate YAML Schema for a Pydantic model.

    This generates a JSON Schema but outputs it in YAML format for better readability.

    Args:
        model: The Pydantic model class
        title: Optional title for the schema

    Returns:
        JSON Schema in YAML format as a string
    """
    schema = generate_json_schema(model, title)
    return yaml.dump(schema, default_flow_style=False, sort_keys=False)


def save_json_schema(model: Type[BaseModel], filename: str, title: str = None) -> None:
    """
    Save JSON Schema to a file.

    Args:
        model: The Pydantic model class
        filename: Path to output file
        title: Optional title for the schema
    """
    schema = generate_json_schema(model, title)
    with open(filename, 'w') as f:
        json.dump(schema, f, indent=2)


def save_yaml_schema(model: Type[BaseModel], filename: str, title: str = None) -> None:
    """
    Save YAML Schema to a file.

    Args:
        model: The Pydantic model class
        filename: Path to output file
        title: Optional title for the schema
    """
    schema_yaml = generate_yaml_schema(model, title)
    with open(filename, 'w') as f:
        f.write(schema_yaml)


def model_from_dict(model_class: Type[T], data: Dict[str, Any], section_name: str = None) -> T:
    """
    Create a model instance from a dictionary.

    Args:
        model_class: The model class to instantiate
        data: Dictionary containing the model data
        section_name: Optional section name for UCI sections

    Returns:
        Instance of the model
    """
    if section_name:
        return model_class(section_name, **data)
    return model_class(**data)


def model_to_dict(model: BaseModel, exclude_none: bool = True, exclude_private: bool = True) -> Dict[str, Any]:
    """
    Convert a model instance to a dictionary.

    Args:
        model: The model instance
        exclude_none: Whether to exclude None values
        exclude_private: Whether to exclude fields starting with _

    Returns:
        Dictionary representation of the model
    """
    data = model.model_dump(exclude_none=exclude_none)

    if exclude_private:
        data = {k: v for k, v in data.items() if not k.startswith('_')}

    return data


def model_from_yaml(model_class: Type[T], yaml_str: str, section_name: str = None) -> T:
    """
    Create a model instance from YAML string.

    Args:
        model_class: The model class to instantiate
        yaml_str: YAML string
        section_name: Optional section name for UCI sections

    Returns:
        Instance of the model
    """
    # Load YAML through OmegaConf for variable interpolation and other features
    omega_conf = OmegaConf.create(yaml_str)
    # Convert to regular Python dict for Pydantic validation
    data = OmegaConf.to_container(omega_conf, resolve=True)
    return model_from_dict(model_class, data, section_name)


def model_from_yaml_file(model_class: Type[T], filename: str, section_name: str = None) -> T:
    """
    Create a model instance from YAML file.

    Args:
        model_class: The model class to instantiate
        filename: Path to YAML file
        section_name: Optional section name for UCI sections

    Returns:
        Instance of the model
    """
    with open(filename, 'r') as f:
        return model_from_yaml(model_class, f.read(), section_name)


def model_from_json(model_class: Type[T], json_str: str, section_name: str = None) -> T:
    """
    Create a model instance from JSON string.

    Args:
        model_class: The model class to instantiate
        json_str: JSON string
        section_name: Optional section name for UCI sections

    Returns:
        Instance of the model
    """
    data = json.loads(json_str)
    return model_from_dict(model_class, data, section_name)


def model_from_json_file(model_class: Type[T], filename: str, section_name: str = None) -> T:
    """
    Create a model instance from JSON file.

    Args:
        model_class: The model class to instantiate
        filename: Path to JSON file
        section_name: Optional section name for UCI sections

    Returns:
        Instance of the model
    """
    with open(filename, 'r') as f:
        return model_from_json(model_class, f.read(), section_name)


def model_to_yaml(model: BaseModel, exclude_none: bool = True, exclude_private: bool = True) -> str:
    """
    Convert a model instance to YAML string.

    Args:
        model: The model instance
        exclude_none: Whether to exclude None values
        exclude_private: Whether to exclude fields starting with _

    Returns:
        YAML string representation
    """
    data = model_to_dict(model, exclude_none, exclude_private)
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def model_to_yaml_file(model: BaseModel, filename: str, exclude_none: bool = True, exclude_private: bool = True) -> None:
    """
    Save a model instance to YAML file.

    Args:
        model: The model instance
        filename: Path to output file
        exclude_none: Whether to exclude None values
        exclude_private: Whether to exclude fields starting with _
    """
    yaml_str = model_to_yaml(model, exclude_none, exclude_private)
    with open(filename, 'w') as f:
        f.write(yaml_str)


def model_to_json(model: BaseModel, exclude_none: bool = True, exclude_private: bool = True, indent: int = 2) -> str:
    """
    Convert a model instance to JSON string.

    Args:
        model: The model instance
        exclude_none: Whether to exclude None values
        exclude_private: Whether to exclude fields starting with _
        indent: Indentation level for pretty printing

    Returns:
        JSON string representation
    """
    data = model_to_dict(model, exclude_none, exclude_private)
    return json.dumps(data, indent=indent)


def model_to_json_file(model: BaseModel, filename: str, exclude_none: bool = True, exclude_private: bool = True, indent: int = 2) -> None:
    """
    Save a model instance to JSON file.

    Args:
        model: The model instance
        filename: Path to output file
        exclude_none: Whether to exclude None values
        exclude_private: Whether to exclude fields starting with _
        indent: Indentation level for pretty printing
    """
    json_str = model_to_json(model, exclude_none, exclude_private, indent)
    with open(filename, 'w') as f:
        f.write(json_str)
