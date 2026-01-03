"""Serial connection management for OpenWRT devices via console."""

import serial
import time
import re
from typing import Optional, Tuple, List, Any


class SerialConnection:
    """Manages serial connections to OpenWRT devices via console (picocom/pyserial)."""

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        timeout: float = 5.0,
        prompt: str = r"root@[^:]+:.*[#\$]",
        login_username: Optional[str] = None,
        login_password: Optional[str] = None,
    ):
        """
        Initialize serial connection parameters.

        Args:
            port: Serial port device (e.g., '/dev/ttyUSB0', 'COM3')
            baudrate: Baud rate for serial communication (default: 115200)
            timeout: Read timeout in seconds (default: 5.0)
            prompt: Regular expression to match the shell prompt
            login_username: Username for login (if needed)
            login_password: Password for login (if needed)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.prompt_pattern = re.compile(prompt)
        self.login_username = login_username
        self.login_password = login_password
        self._serial: Optional[serial.Serial] = None
        self._is_logged_in = False

    def connect(self) -> None:
        """Establish serial connection to the device."""
        if self._serial is not None and self._serial.is_open:
            return

        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )

            # Clear any existing data in the buffer
            time.sleep(0.5)
            self._serial.reset_input_buffer()

            # Send newline to get a fresh prompt
            self._serial.write(b"\n")
            time.sleep(0.5)

            # Check if we need to log in
            if not self._is_logged_in:
                self._handle_login()

        except serial.SerialException as e:
            self._serial = None
            raise ConnectionError(f"Failed to connect to {self.port}: {e}")

    def _handle_login(self) -> None:
        """Handle login if credentials are provided."""
        if not self.login_username:
            # Assume already logged in
            self._is_logged_in = True
            return

        assert self._serial is not None, "Serial connection not established"

        # Read current output
        output = self._read_until_prompt_or_login()

        # Check if we see a login prompt
        if "login:" in output.lower():
            # Send username
            self._serial.write(f"{self.login_username}\n".encode())
            time.sleep(0.5)

            # Check for password prompt
            output = self._serial.read(self._serial.in_waiting or 1).decode(
                "utf-8", errors="ignore"
            )

            if "password:" in output.lower() and self.login_password:
                self._serial.write(f"{self.login_password}\n".encode())
                time.sleep(1)

                # Wait for prompt after login
                self._wait_for_prompt()

        self._is_logged_in = True

    def _read_until_prompt_or_login(self, timeout: Optional[float] = None) -> str:
        """Read until we see a prompt or login."""
        if timeout is None:
            timeout = self.timeout

        assert self._serial is not None, "Serial connection not established"

        output = ""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._serial.in_waiting:
                chunk = self._serial.read(self._serial.in_waiting).decode("utf-8", errors="ignore")
                output += chunk

                # Check for prompt or login
                if self.prompt_pattern.search(output) or "login:" in output.lower():
                    break
            time.sleep(0.1)

        return output

    def _wait_for_prompt(self, timeout: Optional[float] = None) -> str:
        """Wait for the shell prompt and return all output."""
        if timeout is None:
            timeout = self.timeout

        assert self._serial is not None, "Serial connection not established"

        output = ""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._serial.in_waiting:
                chunk = self._serial.read(self._serial.in_waiting).decode("utf-8", errors="ignore")
                output += chunk

                # Check if we have a prompt
                if self.prompt_pattern.search(output):
                    break
            time.sleep(0.1)

        return output

    def disconnect(self) -> None:
        """Close the serial connection."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
            self._serial = None
            self._is_logged_in = False

    def execute(self, command: str) -> Tuple[str, str, int]:
        """
        Execute a command on the remote device.

        Args:
            command: The command to execute

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if self._serial is None or not self._serial.is_open:
            self.connect()

        assert self._serial is not None, "Serial connection not established"

        # Clear input buffer
        self._serial.reset_input_buffer()

        # Send command
        self._serial.write(f"{command}\n".encode())
        time.sleep(0.2)

        # Wait for command output and prompt
        output = self._wait_for_prompt()

        # Remove the echoed command from the output
        lines = output.split("\n")
        # Filter out the command echo and prompt lines
        filtered_lines = []
        for line in lines:
            # Skip the echoed command and prompt lines
            if command in line or self.prompt_pattern.search(line):
                continue
            filtered_lines.append(line)

        stdout = "\n".join(filtered_lines).strip()

        # Get exit code by running a separate command
        self._serial.write(b"echo $?\n")
        time.sleep(0.2)
        exit_output = self._wait_for_prompt()

        # Extract exit code
        exit_code = 0
        for line in exit_output.split("\n"):
            line = line.strip()
            if line.isdigit():
                exit_code = int(line)
                break

        # For now, we don't separate stderr from stdout in serial
        stderr = ""

        return (stdout, stderr, exit_code)

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

    def __enter__(self) -> "SerialConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()
