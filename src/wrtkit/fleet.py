"""Fleet management for multiple OpenWRT devices."""

import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, cast

from omegaconf import OmegaConf
from pydantic import BaseModel, Field

from .config import UCIConfig


class FleetDefaults(BaseModel):
    """Default settings applied to all devices in the fleet."""

    timeout: int = Field(default=30, description="Connection timeout in seconds")
    username: str = Field(default="root", description="Default SSH username")
    commit_delay: int = Field(default=10, description="Seconds to wait before coordinated commit")


class FleetDevice(BaseModel):
    """Definition of a single device in the fleet."""

    target: str = Field(..., description="Device address (IP, hostname, or serial port)")
    username: Optional[str] = Field(default=None, description="SSH username override")
    password: Optional[str] = Field(default=None, description="SSH/login password")
    key_file: Optional[str] = Field(default=None, description="SSH private key file")
    timeout: Optional[int] = Field(default=None, description="Connection timeout override")
    configs: List[str] = Field(default_factory=list, description="Config files to merge")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")


class FleetConfig(BaseModel):
    """Fleet inventory configuration."""

    defaults: FleetDefaults = Field(default_factory=FleetDefaults)
    config_layers: Dict[str, str] = Field(
        default_factory=dict, description="Named config file paths for interpolation"
    )
    devices: Dict[str, FleetDevice] = Field(
        default_factory=dict, description="Device definitions keyed by name"
    )


def load_fleet(fleet_file: str) -> FleetConfig:
    """
    Load a fleet inventory file.

    Uses OmegaConf for variable interpolation including:
    - Environment variables: ${oc.env:VAR_NAME}
    - Config layer references: ${config_layers.base}

    Args:
        fleet_file: Path to the fleet YAML file

    Returns:
        FleetConfig instance
    """
    fleet_path = Path(fleet_file)
    if not fleet_path.exists():
        raise FileNotFoundError(f"Fleet file not found: {fleet_file}")

    with open(fleet_path, "r") as f:
        yaml_content = f.read()

    # Load through OmegaConf for interpolation
    omega_conf = OmegaConf.create(yaml_content)

    # Resolve interpolations
    data = OmegaConf.to_container(omega_conf, resolve=True)
    if not isinstance(data, dict):
        raise ValueError("Fleet file must be a YAML dictionary")

    return FleetConfig.model_validate(data)


def merge_device_configs(
    device: FleetDevice,
    fleet_path: Path,
) -> UCIConfig:
    """
    Merge multiple config files for a device using OmegaConf.

    Config files are merged in order, with later files overriding earlier ones.

    Args:
        device: The device definition with config file list
        fleet_path: Path to the fleet file (for resolving relative paths)

    Returns:
        Merged UCIConfig instance
    """
    if not device.configs:
        return UCIConfig()

    base_dir = fleet_path.parent

    # Load and merge all config files
    merged_omega: Optional[Any] = None

    for config_path in device.configs:
        # Resolve relative paths from fleet file location
        full_path = (
            base_dir / config_path if not Path(config_path).is_absolute() else Path(config_path)
        )

        if not full_path.exists():
            raise FileNotFoundError(f"Config file not found: {full_path}")

        with open(full_path, "r") as f:
            yaml_content = f.read()

        config_omega = OmegaConf.create(yaml_content)

        if merged_omega is None:
            merged_omega = config_omega
        else:
            merged_omega = OmegaConf.merge(merged_omega, config_omega)

    if merged_omega is None:
        return UCIConfig()

    # Resolve all interpolations and convert to dict
    data = OmegaConf.to_container(merged_omega, resolve=True)
    if not isinstance(data, dict):
        raise ValueError("Merged config must be a dictionary")

    return UCIConfig.from_dict(cast(Dict[str, Any], data))


def filter_devices(
    fleet: FleetConfig,
    target: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, FleetDevice]:
    """
    Filter fleet devices by name/glob pattern and/or tags.

    Args:
        fleet: The fleet configuration
        target: Device name or glob pattern (e.g., "ap-*")
        tags: List of tags (AND logic - device must have all tags)

    Returns:
        Dictionary of matching devices keyed by name
    """
    result: Dict[str, FleetDevice] = {}

    for name, device in fleet.devices.items():
        # Check target filter (name or glob)
        if target is not None:
            if not fnmatch.fnmatch(name, target):
                continue

        # Check tags filter (AND logic)
        if tags is not None:
            device_tags: Set[str] = set(device.tags)
            required_tags: Set[str] = set(tags)
            if not required_tags.issubset(device_tags):
                continue

        result[name] = device

    return result


def get_device_connection_params(
    device: FleetDevice,
    defaults: FleetDefaults,
) -> Dict[str, Any]:
    """
    Get connection parameters for a device, applying defaults.

    Args:
        device: The device definition
        defaults: Fleet defaults to apply

    Returns:
        Dictionary with connection parameters
    """
    return {
        "target": device.target,
        "username": device.username or defaults.username,
        "password": device.password,
        "key_file": device.key_file,
        "timeout": device.timeout or defaults.timeout,
    }
