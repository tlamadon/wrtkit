"""Fleet execution engine with two-phase coordinated updates."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from .config import ConfigDiff
from .fleet import (
    FleetConfig,
    FleetDevice,
    filter_devices,
    get_device_connection_params,
    merge_device_configs,
)
from .serial_connection import SerialConnection
from .ssh import SSHConnection

Connection = Union[SSHConnection, SerialConnection]


def parse_target(target: str) -> dict:
    """Parse a target string into connection parameters."""
    result = {
        "type": "ssh",
        "host": target,
        "port": 22,
        "username": "root",
    }

    # Check for serial port
    if target.startswith("/dev/") or target.startswith("COM"):
        result["type"] = "serial"
        result["port"] = target
        return result

    # Parse user@host:port format
    if "@" in target:
        user_part, host_part = target.split("@", 1)
        result["username"] = user_part
        target = host_part

    if ":" in target and not target.startswith("["):
        host, port = target.rsplit(":", 1)
        result["host"] = host
        result["port"] = int(port)
    else:
        result["host"] = target

    return result


def create_connection(
    target: str,
    password: Optional[str],
    key_file: Optional[str],
    timeout: int,
    username: str = "root",
) -> Connection:
    """Create a connection based on target type."""
    params = parse_target(target)

    if params["type"] == "serial":
        return SerialConnection(
            port=params["port"],
            login_username=username,
            login_password=password,
            timeout=float(timeout),
        )
    else:
        return SSHConnection(
            host=params["host"],
            port=params["port"],
            username=username,
            password=password,
            key_filename=key_file,
            timeout=timeout,
        )


@dataclass
class DeviceResult:
    """Result of operations on a single device."""

    name: str
    target: str
    success: bool
    error: Optional[str] = None
    diff: Optional[ConfigDiff] = None
    changes_count: int = 0


@dataclass
class FleetResult:
    """Result of fleet-wide operations."""

    devices: Dict[str, DeviceResult] = field(default_factory=dict)
    phase: str = "unknown"
    aborted: bool = False
    abort_reason: Optional[str] = None

    @property
    def success_count(self) -> int:
        return sum(1 for d in self.devices.values() if d.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for d in self.devices.values() if not d.success)

    @property
    def total_count(self) -> int:
        return len(self.devices)

    @property
    def all_successful(self) -> bool:
        return all(d.success for d in self.devices.values())


class FleetExecutor:
    """
    Executes fleet operations with two-phase coordinated updates.

    Phase 1 (Stage): Push UCI commands to all devices in parallel without committing.
                     Fail fast if any device fails.
    Phase 2 (Commit): Send coordinated commit commands to all devices simultaneously.
    """

    def __init__(
        self,
        fleet: FleetConfig,
        fleet_path: Path,
        on_device_start: Optional[Callable[[str, str], None]] = None,
        on_device_complete: Optional[Callable[[str, DeviceResult], None]] = None,
        on_phase_start: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize fleet executor.

        Args:
            fleet: Fleet configuration
            fleet_path: Path to fleet file (for resolving relative paths)
            on_device_start: Callback when starting work on a device (name, target)
            on_device_complete: Callback when device work completes (name, result)
            on_phase_start: Callback when a phase starts (phase_name)
        """
        self.fleet = fleet
        self.fleet_path = fleet_path
        self.on_device_start = on_device_start
        self.on_device_complete = on_device_complete
        self.on_phase_start = on_phase_start
        self._connections: Dict[str, Connection] = {}
        self._staged_devices: Dict[str, ConfigDiff] = {}

    def _notify_device_start(self, name: str, target: str) -> None:
        if self.on_device_start:
            self.on_device_start(name, target)

    def _notify_device_complete(self, name: str, result: DeviceResult) -> None:
        if self.on_device_complete:
            self.on_device_complete(name, result)

    def _notify_phase_start(self, phase: str) -> None:
        if self.on_phase_start:
            self.on_phase_start(phase)

    def preview(
        self,
        target: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_workers: int = 5,
    ) -> FleetResult:
        """
        Preview changes for targeted devices without applying.

        Args:
            target: Device name or glob pattern
            tags: List of tags to filter by
            max_workers: Maximum parallel connections

        Returns:
            FleetResult with diff information for each device
        """
        devices = filter_devices(self.fleet, target, tags)
        result = FleetResult(phase="preview")

        if not devices:
            return result

        self._notify_phase_start("preview")

        def preview_device(name: str, device: FleetDevice) -> DeviceResult:
            self._notify_device_start(name, device.target)
            try:
                # Merge configs for this device
                config = merge_device_configs(device, self.fleet_path)

                # Create connection
                params = get_device_connection_params(device, self.fleet.defaults)
                conn = create_connection(
                    target=params["target"],
                    password=params["password"],
                    key_file=params["key_file"],
                    timeout=params["timeout"],
                    username=params["username"],
                )

                with conn:
                    # Compute diff
                    diff = config.diff(conn, show_remote_only=True, verbose=False)  # type: ignore[arg-type]

                    changes = len(diff.to_add) + len(diff.to_modify) + len(diff.to_remove)
                    return DeviceResult(
                        name=name,
                        target=device.target,
                        success=True,
                        diff=diff,
                        changes_count=changes,
                    )

            except Exception as e:
                return DeviceResult(
                    name=name,
                    target=device.target,
                    success=False,
                    error=str(e),
                )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(preview_device, name, device): name
                for name, device in devices.items()
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    device_result = future.result()
                except Exception as e:
                    device_result = DeviceResult(
                        name=name,
                        target=devices[name].target,
                        success=False,
                        error=str(e),
                    )

                result.devices[name] = device_result
                self._notify_device_complete(name, device_result)

        return result

    def stage(
        self,
        target: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_workers: int = 5,
        remove_unmanaged: bool = False,
    ) -> FleetResult:
        """
        Stage changes to devices (Phase 1).

        Pushes UCI commands without committing. Fails fast on any error.

        Args:
            target: Device name or glob pattern
            tags: List of tags to filter by
            max_workers: Maximum parallel connections
            remove_unmanaged: Remove settings not in config

        Returns:
            FleetResult with staging results
        """
        devices = filter_devices(self.fleet, target, tags)
        result = FleetResult(phase="stage")
        self._staged_devices.clear()
        self._connections.clear()

        if not devices:
            return result

        self._notify_phase_start("stage")

        def stage_device(name: str, device: FleetDevice) -> DeviceResult:
            self._notify_device_start(name, device.target)
            try:
                # Merge configs for this device
                config = merge_device_configs(device, self.fleet_path)

                # Create connection
                params = get_device_connection_params(device, self.fleet.defaults)
                conn = create_connection(
                    target=params["target"],
                    password=params["password"],
                    key_file=params["key_file"],
                    timeout=params["timeout"],
                    username=params["username"],
                )

                conn.connect()

                # Apply diff without commit/reload
                diff = config.apply_diff(
                    conn,  # type: ignore[arg-type]
                    remove_unmanaged=remove_unmanaged,
                    dry_run=False,
                    auto_commit=False,
                    auto_reload=False,
                    verbose=False,
                )

                changes = len(diff.to_add) + len(diff.to_modify) + len(diff.to_remove)

                # Keep connection open for commit phase
                self._connections[name] = conn
                self._staged_devices[name] = diff

                return DeviceResult(
                    name=name,
                    target=device.target,
                    success=True,
                    diff=diff,
                    changes_count=changes,
                )

            except Exception as e:
                return DeviceResult(
                    name=name,
                    target=device.target,
                    success=False,
                    error=str(e),
                )

        # Execute staging in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(stage_device, name, device): name
                for name, device in devices.items()
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    device_result = future.result()
                except Exception as e:
                    device_result = DeviceResult(
                        name=name,
                        target=devices[name].target,
                        success=False,
                        error=str(e),
                    )

                result.devices[name] = device_result
                self._notify_device_complete(name, device_result)

                # Fail fast: abort if any device fails
                if not device_result.success:
                    result.aborted = True
                    result.abort_reason = f"Device '{name}' failed: {device_result.error}"
                    # Cancel remaining futures (best effort)
                    for f in futures:
                        f.cancel()
                    break

        # If aborted, rollback staged changes
        if result.aborted:
            self._rollback_all()

        return result

    def commit(self, delay: Optional[int] = None) -> FleetResult:
        """
        Commit staged changes on all devices (Phase 2).

        Sends coordinated commit commands with optional delay for synchronization.

        Args:
            delay: Seconds to delay before commit (uses fleet default if None)

        Returns:
            FleetResult with commit results
        """
        result = FleetResult(phase="commit")

        if not self._connections:
            return result

        commit_delay = delay if delay is not None else self.fleet.defaults.commit_delay
        self._notify_phase_start("commit")

        def commit_device(name: str, conn: Connection) -> DeviceResult:
            target = conn.host if hasattr(conn, "host") else getattr(conn, "port", "unknown")
            self._notify_device_start(name, str(target))
            try:
                # Execute commit and reload via background command
                # This ensures all devices start the commit at roughly the same time
                commit_cmd = (
                    f"nohup sh -c 'sleep {commit_delay} && "
                    f"uci commit && "
                    f"/etc/init.d/network restart && "
                    f"wifi reload' > /dev/null 2>&1 &"
                )

                conn.execute(commit_cmd)

                return DeviceResult(
                    name=name,
                    target=str(target),
                    success=True,
                )

            except Exception as e:
                return DeviceResult(
                    name=name,
                    target=str(target),
                    success=False,
                    error=str(e),
                )
            finally:
                try:
                    conn.disconnect()
                except Exception:
                    pass

        # Send commit commands to all devices in parallel
        with ThreadPoolExecutor(max_workers=len(self._connections)) as executor:
            futures = {
                executor.submit(commit_device, name, conn): name
                for name, conn in self._connections.items()
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    device_result = future.result()
                except Exception as e:
                    device_result = DeviceResult(
                        name=name,
                        target="unknown",
                        success=False,
                        error=str(e),
                    )

                result.devices[name] = device_result
                self._notify_device_complete(name, device_result)

        self._connections.clear()
        self._staged_devices.clear()

        return result

    def apply(
        self,
        target: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_workers: int = 5,
        remove_unmanaged: bool = False,
        commit_delay: Optional[int] = None,
    ) -> tuple[FleetResult, FleetResult]:
        """
        Apply changes to fleet devices with two-phase execution.

        Phase 1: Stage all changes in parallel (fail fast)
        Phase 2: Coordinated commit if staging succeeded

        Args:
            target: Device name or glob pattern
            tags: List of tags to filter by
            max_workers: Maximum parallel connections
            remove_unmanaged: Remove settings not in config
            commit_delay: Override default commit delay

        Returns:
            Tuple of (stage_result, commit_result)
        """
        # Phase 1: Stage
        stage_result = self.stage(
            target=target,
            tags=tags,
            max_workers=max_workers,
            remove_unmanaged=remove_unmanaged,
        )

        # If staging failed or was aborted, don't proceed to commit
        if stage_result.aborted or not stage_result.all_successful:
            return stage_result, FleetResult(phase="commit", aborted=True)

        # Phase 2: Commit
        commit_result = self.commit(delay=commit_delay)

        return stage_result, commit_result

    def _rollback_all(self) -> None:
        """Rollback staged changes on all devices."""
        for name, conn in self._connections.items():
            try:
                # Revert UCI changes
                conn.execute("uci revert")
                conn.disconnect()
            except Exception:
                pass

        self._connections.clear()
        self._staged_devices.clear()

    def cleanup(self) -> None:
        """Clean up any open connections."""
        for conn in self._connections.values():
            try:
                conn.disconnect()
            except Exception:
                pass
        self._connections.clear()
        self._staged_devices.clear()
