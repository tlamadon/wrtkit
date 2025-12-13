"""Main UCI configuration class."""

from typing import List, Optional, Dict, Set
from .base import UCICommand
from .network import NetworkConfig
from .wireless import WirelessConfig
from .dhcp import DHCPConfig
from .firewall import FirewallConfig
from .ssh import SSHConnection


class ConfigDiff:
    """Represents the difference between two configurations."""

    def __init__(self):
        self.to_add: List[UCICommand] = []
        self.to_remove: List[UCICommand] = []
        self.to_modify: List[tuple[UCICommand, UCICommand]] = []

    def is_empty(self) -> bool:
        """Check if there are no differences."""
        return not (self.to_add or self.to_remove or self.to_modify)

    def __str__(self) -> str:
        """Format the diff for display."""
        lines = []

        if self.to_add:
            lines.append("Commands to add:")
            for cmd in self.to_add:
                lines.append(f"  + {cmd.to_string()}")

        if self.to_remove:
            lines.append("\nCommands to remove:")
            for cmd in self.to_remove:
                lines.append(f"  - {cmd.to_string()}")

        if self.to_modify:
            lines.append("\nCommands to modify:")
            for old_cmd, new_cmd in self.to_modify:
                lines.append(f"  - {old_cmd.to_string()}")
                lines.append(f"  + {new_cmd.to_string()}")

        if not lines:
            return "No differences found."

        return "\n".join(lines)


class UCIConfig:
    """Main UCI configuration class."""

    def __init__(self):
        self.network = NetworkConfig()
        self.wireless = WirelessConfig()
        self.dhcp = DHCPConfig()
        self.firewall = FirewallConfig()

    def get_all_commands(self) -> List[UCICommand]:
        """Get all UCI commands from all configuration sections."""
        commands = []
        commands.extend(self.network.get_commands())
        commands.extend(self.wireless.get_commands())
        commands.extend(self.dhcp.get_commands())
        commands.extend(self.firewall.get_commands())
        return commands

    def to_script(self, include_commit: bool = True, include_reload: bool = True) -> str:
        """
        Generate a shell script with all UCI commands.

        Args:
            include_commit: Whether to include 'uci commit' command
            include_reload: Whether to include network restart and wifi reload

        Returns:
            A shell script as a string
        """
        lines = ["#!/bin/sh", ""]

        commands = self.get_all_commands()
        for cmd in commands:
            lines.append(cmd.to_string())

        if include_commit:
            lines.append("")
            lines.append("uci commit")

        if include_reload:
            lines.append("/etc/init.d/network restart")
            lines.append("wifi reload")

        return "\n".join(lines)

    def _parse_remote_config(self, ssh: SSHConnection) -> List[UCICommand]:
        """
        Parse the remote UCI configuration into commands.

        This is a simplified parser. A full implementation would need
        to handle all UCI export format details.
        """
        commands = []
        packages = ["network", "wireless", "dhcp", "firewall"]

        for package in packages:
            try:
                config_str = ssh.get_uci_config(package)
                # Parse the UCI export format
                # This is simplified - a full implementation would be more robust
                for line in config_str.strip().split("\n"):
                    if not line or line.startswith("#"):
                        continue
                    # UCI export format: package.section=type or package.section.option=value
                    if "=" in line:
                        parts = line.split("=", 1)
                        path = parts[0].strip()
                        value = parts[1].strip().strip("'\"")

                        # Determine if this is a section or option
                        path_parts = path.split(".")
                        if len(path_parts) == 2:
                            # Section definition
                            commands.append(UCICommand("set", path, value))
                        elif len(path_parts) == 3:
                            # Option
                            commands.append(UCICommand("set", path, value))
            except Exception as e:
                # If we can't get a package, just skip it
                print(f"Warning: Could not retrieve {package} config: {e}")
                continue

        return commands

    def diff(self, ssh: SSHConnection) -> ConfigDiff:
        """
        Compare this configuration with the remote device configuration.

        Args:
            ssh: SSH connection to the remote device

        Returns:
            A ConfigDiff object describing the differences
        """
        local_commands = self.get_all_commands()
        remote_commands = self._parse_remote_config(ssh)

        diff = ConfigDiff()

        # Create sets for comparison
        local_set = {(cmd.path, cmd.value) for cmd in local_commands}
        remote_set = {(cmd.path, cmd.value) for cmd in remote_commands}

        # Commands in local but not in remote
        for cmd in local_commands:
            key = (cmd.path, cmd.value)
            if key not in remote_set:
                # Check if path exists in remote with different value
                remote_paths = {c.path for c in remote_commands}
                if cmd.path in remote_paths:
                    # Find the remote command with same path
                    remote_cmd = next(c for c in remote_commands if c.path == cmd.path)
                    diff.to_modify.append((remote_cmd, cmd))
                else:
                    diff.to_add.append(cmd)

        # Commands in remote but not in local
        for cmd in remote_commands:
            key = (cmd.path, cmd.value)
            local_paths = {c.path for c in local_commands}
            if key not in local_set and cmd.path not in local_paths:
                diff.to_remove.append(cmd)

        return diff

    def apply(
        self,
        ssh: SSHConnection,
        dry_run: bool = False,
        auto_commit: bool = True,
        auto_reload: bool = True,
    ) -> None:
        """
        Apply this configuration to a remote device.

        Args:
            ssh: SSH connection to the remote device
            dry_run: If True, only show what would be done
            auto_commit: If True, automatically commit changes
            auto_reload: If True, automatically reload network and wireless
        """
        commands = self.get_all_commands()

        if dry_run:
            print("Dry run - commands that would be executed:")
            for cmd in commands:
                print(f"  {cmd.to_string()}")
            if auto_commit:
                print("  uci commit")
            if auto_reload:
                print("  /etc/init.d/network restart")
                print("  wifi reload")
            return

        # Execute commands
        for cmd in commands:
            stdout, stderr, exit_code = ssh.execute_uci_command(cmd.to_string())
            if exit_code != 0:
                raise RuntimeError(
                    f"Failed to execute command '{cmd.to_string()}': {stderr}"
                )

        # Commit changes
        if auto_commit:
            ssh.commit_changes()

        # Reload configuration
        if auto_reload:
            ssh.reload_config()

    def save_to_file(self, filename: str, include_commit: bool = True, include_reload: bool = True) -> None:
        """
        Save the configuration to a shell script file.

        Args:
            filename: Path to the output file
            include_commit: Whether to include 'uci commit' command
            include_reload: Whether to include network restart and wifi reload
        """
        script = self.to_script(include_commit=include_commit, include_reload=include_reload)
        with open(filename, "w") as f:
            f.write(script)
