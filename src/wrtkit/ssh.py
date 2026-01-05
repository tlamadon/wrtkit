"""SSH connection management for remote OpenWRT devices."""

import paramiko
from typing import Optional, Tuple, List, Set
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

    def reload_config(
        self,
        reload_dhcp: bool = True,
        changed_packages: Optional[Set[str]] = None,
    ) -> List[str]:
        """
        Reload network configuration and wireless settings.

        Only restarts services related to packages that actually changed.

        Args:
            reload_dhcp: If True, also restart dnsmasq to apply DHCP changes
                (only when dhcp package changed or changed_packages is None)
            changed_packages: Set of package names that have changes.
                If None, restarts all services (legacy behavior).
                If empty set, restarts nothing.

        Returns:
            List of commands that were executed.
        """
        # If changed_packages is empty set, nothing to restart
        if changed_packages is not None and len(changed_packages) == 0:
            return []

        commands: List[str] = []

        # Determine which services need restart based on changed packages
        if changed_packages is None:
            # Legacy behavior: restart all
            commands.append("/etc/init.d/network restart")
            commands.append("wifi reload")
            if reload_dhcp:
                commands.append("/etc/init.d/dnsmasq restart")
        else:
            # Package-aware restart
            # network and sqm changes require network restart
            if "network" in changed_packages or "sqm" in changed_packages:
                commands.append("/etc/init.d/network restart")

            # wireless changes require wifi reload
            if "wireless" in changed_packages:
                commands.append("wifi reload")

            # dhcp changes require dnsmasq restart
            if "dhcp" in changed_packages and reload_dhcp:
                commands.append("/etc/init.d/dnsmasq restart")

            # firewall changes require firewall reload
            if "firewall" in changed_packages:
                commands.append("/etc/init.d/firewall reload")

        # Execute commands (deduplicated by using list, no duplicates added above)
        for cmd in commands:
            stdout, stderr, exit_code = self.execute(cmd)
            if exit_code != 0:
                print(f"Warning: {cmd} returned non-zero exit code: {stderr}")
            time.sleep(1)

        return commands

    def __enter__(self) -> "SSHConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
