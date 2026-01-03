"""SSH connection management for remote OpenWRT devices."""

import paramiko
from typing import Optional, Tuple, List
import time


class SSHConnection:
    """Manages SSH connections to OpenWRT devices."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize SSH connection parameters.

        Args:
            host: The hostname or IP address of the OpenWRT device
            port: SSH port (default: 22)
            username: SSH username (default: root)
            password: SSH password
            key_filename: Path to SSH private key file
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.timeout = timeout
        self._client: Optional[paramiko.SSHClient] = None

    def connect(self) -> None:
        """Establish SSH connection to the device."""
        if self._client is not None:
            return

        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self._client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=self.timeout,
            )
        except Exception as e:
            self._client = None
            raise ConnectionError(f"Failed to connect to {self.host}: {e}")

    def disconnect(self) -> None:
        """Close the SSH connection."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def execute(self, command: str) -> Tuple[str, str, int]:
        """
        Execute a command on the remote device.

        Args:
            command: The command to execute

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if self._client is None:
            self.connect()

        stdin, stdout, stderr = self._client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()

        return (
            stdout.read().decode("utf-8"),
            stderr.read().decode("utf-8"),
            exit_code,
        )

    def execute_uci_command(self, command: str) -> Tuple[str, str, int]:
        """
        Execute a UCI command on the remote device.

        Args:
            command: The UCI command to execute

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        return self.execute(command)

    def get_uci_config(self, package: str) -> str:
        """
        Retrieve the current UCI configuration for a package.

        Args:
            package: The UCI package name (e.g., 'network', 'wireless')

        Returns:
            The UCI configuration as a string
        """
        stdout, stderr, exit_code = self.execute(f"uci export {package}")
        if exit_code != 0:
            raise RuntimeError(f"Failed to get UCI config for {package}: {stderr}")
        return stdout

    def commit_changes(self, packages: Optional[List[str]] = None) -> None:
        """
        Commit UCI changes.

        Args:
            packages: List of packages to commit. If None, commits all changes.
        """
        if packages:
            for package in packages:
                stdout, stderr, exit_code = self.execute(f"uci commit {package}")
                if exit_code != 0:
                    raise RuntimeError(f"Failed to commit {package}: {stderr}")
        else:
            stdout, stderr, exit_code = self.execute("uci commit")
            if exit_code != 0:
                raise RuntimeError(f"Failed to commit changes: {stderr}")

    def reload_config(self, reload_dhcp: bool = True) -> None:
        """
        Reload network configuration and wireless settings.

        Args:
            reload_dhcp: If True, also restart dnsmasq to apply DHCP changes
        """
        commands = [
            "/etc/init.d/network restart",
            "wifi reload",
        ]

        if reload_dhcp:
            commands.append("/etc/init.d/dnsmasq restart")

        for cmd in commands:
            stdout, stderr, exit_code = self.execute(cmd)
            if exit_code != 0:
                print(f"Warning: {cmd} returned non-zero exit code: {stderr}")
            time.sleep(1)

    def __enter__(self) -> "SSHConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
