"""Network testing configuration and models."""

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from omegaconf import OmegaConf
from pydantic import BaseModel, Field, model_validator

from .fleet import FleetConfig, FleetDevice, load_fleet


class PingTest(BaseModel):
    """Ping test definition."""

    name: str = Field(..., description="Unique test name")
    type: Literal["ping"] = Field(..., description="Test type")
    source: str = Field(..., description="Source device name from fleet")
    destination: str = Field(..., description="Destination device name from fleet, or IP/hostname")
    count: int = Field(default=4, description="Number of ping requests")
    interval: float = Field(default=1.0, description="Seconds between pings")
    timeout: int = Field(default=5, description="Per-ping timeout in seconds")


class IperfTest(BaseModel):
    """Iperf test definition."""

    name: str = Field(..., description="Unique test name")
    type: Literal["iperf"] = Field(..., description="Test type")
    server: str = Field(..., description="Server device name from fleet")
    client: str = Field(..., description="Client device name from fleet")
    duration: int = Field(default=10, description="Test duration in seconds")
    parallel: int = Field(default=1, description="Number of parallel streams")
    reverse: bool = Field(default=False, description="Reverse direction (server sends)")
    protocol: Literal["tcp", "udp"] = Field(default="tcp", description="Transport protocol")
    bitrate: Optional[str] = Field(
        default=None, description="Target bitrate for UDP (e.g., '100M')"
    )
    port: int = Field(default=5201, description="Iperf server port")


TestDefinition = Union[PingTest, IperfTest]


class TestConfig(BaseModel):
    """Test configuration file structure."""

    fleet_file: str = Field(..., description="Path to fleet inventory file")
    tests: List[TestDefinition] = Field(
        default_factory=list, description="List of test definitions"
    )

    @model_validator(mode="before")
    @classmethod
    def parse_tests(cls, data: Any) -> Any:
        """Parse test definitions based on their type."""
        if isinstance(data, dict) and "tests" in data:
            parsed_tests: List[Union[PingTest, IperfTest]] = []
            for test in data["tests"]:
                if isinstance(test, dict):
                    test_type = test.get("type")
                    if test_type == "ping":
                        parsed_tests.append(PingTest.model_validate(test))
                    elif test_type == "iperf":
                        parsed_tests.append(IperfTest.model_validate(test))
                    else:
                        raise ValueError(f"Unknown test type: {test_type}")
                else:
                    parsed_tests.append(test)
            data["tests"] = parsed_tests
        return data


class ResolvedPingTest(BaseModel):
    """Ping test with resolved device information."""

    name: str
    source_device: str
    source_target: str
    destination: str  # Resolved IP/hostname
    count: int
    interval: float
    timeout: int
    source_params: Dict[str, Any]  # Connection params for source


class ResolvedIperfTest(BaseModel):
    """Iperf test with resolved device information."""

    name: str
    server_device: str
    server_target: str
    client_device: str
    client_target: str
    duration: int
    parallel: int
    reverse: bool
    protocol: Literal["tcp", "udp"]
    bitrate: Optional[str]
    port: int
    server_params: Dict[str, Any]  # Connection params for server
    client_params: Dict[str, Any]  # Connection params for client


ResolvedTest = Union[ResolvedPingTest, ResolvedIperfTest]


def load_test_config(test_file: str) -> TestConfig:
    """
    Load a test configuration file.

    Uses OmegaConf for variable interpolation.

    Args:
        test_file: Path to the test YAML file

    Returns:
        TestConfig instance
    """
    test_path = Path(test_file)
    if not test_path.exists():
        raise FileNotFoundError(f"Test config file not found: {test_file}")

    with open(test_path, "r") as f:
        yaml_content = f.read()

    omega_conf = OmegaConf.create(yaml_content)
    data = OmegaConf.to_container(omega_conf, resolve=True)
    if not isinstance(data, dict):
        raise ValueError("Test config file must be a YAML dictionary")

    return TestConfig.model_validate(data)


def _get_device_connection_params(
    device: FleetDevice,
    defaults: Any,
) -> Dict[str, Any]:
    """Get connection parameters for a device, applying defaults."""
    return {
        "target": device.target,
        "username": device.username or defaults.username,
        "password": device.password,
        "key_file": device.key_file,
        "timeout": device.timeout or defaults.timeout,
    }


def _resolve_destination(
    destination: str,
    fleet: FleetConfig,
) -> str:
    """
    Resolve a destination to an IP/hostname.

    If destination matches a fleet device name, returns that device's target.
    Otherwise, returns the destination as-is (assumed to be IP/hostname).
    """
    if destination in fleet.devices:
        return fleet.devices[destination].target
    return destination


def resolve_tests(
    test_config: TestConfig,
    test_file_path: Path,
) -> List[ResolvedTest]:
    """
    Resolve test definitions with fleet device information.

    Args:
        test_config: The test configuration
        test_file_path: Path to the test config file (for resolving fleet file)

    Returns:
        List of resolved tests with connection parameters
    """
    # Load the fleet file (relative to test config location)
    fleet_path = test_file_path.parent / test_config.fleet_file
    if not fleet_path.exists():
        # Try absolute path
        fleet_path = Path(test_config.fleet_file)

    fleet = load_fleet(str(fleet_path))
    resolved: List[ResolvedTest] = []

    for test in test_config.tests:
        if isinstance(test, PingTest):
            # Validate source device exists
            if test.source not in fleet.devices:
                raise ValueError(
                    f"Test '{test.name}': source device '{test.source}' not found in fleet"
                )

            source_device = fleet.devices[test.source]
            destination = _resolve_destination(test.destination, fleet)

            resolved.append(
                ResolvedPingTest(
                    name=test.name,
                    source_device=test.source,
                    source_target=source_device.target,
                    destination=destination,
                    count=test.count,
                    interval=test.interval,
                    timeout=test.timeout,
                    source_params=_get_device_connection_params(source_device, fleet.defaults),
                )
            )

        elif isinstance(test, IperfTest):
            # Validate server device exists
            if test.server not in fleet.devices:
                raise ValueError(
                    f"Test '{test.name}': server device '{test.server}' not found in fleet"
                )
            # Validate client device exists
            if test.client not in fleet.devices:
                raise ValueError(
                    f"Test '{test.name}': client device '{test.client}' not found in fleet"
                )

            server_device = fleet.devices[test.server]
            client_device = fleet.devices[test.client]

            resolved.append(
                ResolvedIperfTest(
                    name=test.name,
                    server_device=test.server,
                    server_target=server_device.target,
                    client_device=test.client,
                    client_target=client_device.target,
                    duration=test.duration,
                    parallel=test.parallel,
                    reverse=test.reverse,
                    protocol=test.protocol,
                    bitrate=test.bitrate,
                    port=test.port,
                    server_params=_get_device_connection_params(server_device, fleet.defaults),
                    client_params=_get_device_connection_params(client_device, fleet.defaults),
                )
            )

    return resolved
