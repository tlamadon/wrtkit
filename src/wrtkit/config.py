"""Main UCI configuration class."""

from typing import List, Dict
from .base import UCICommand
from .network import NetworkConfig, NetworkInterface, NetworkDevice
from .wireless import WirelessConfig, WirelessRadio, WirelessInterface
from .dhcp import DHCPConfig, DHCPSection
from .firewall import FirewallConfig, FirewallZone, FirewallForwarding
from .ssh import SSHConnection


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'      # For additions (+)
    YELLOW = '\033[93m'     # For modifications (~)
    CYAN = '\033[96m'       # For remote-only (*)
    RED = '\033[91m'        # For removals (-)
    RESET = '\033[0m'       # Reset to default
    BOLD = '\033[1m'        # Bold text
    DIM = '\033[2m'         # Dim text


class ConfigDiff:
    """Represents the difference between two configurations."""

    def __init__(self):
        self.to_add: List[UCICommand] = []
        self.to_remove: List[UCICommand] = []
        self.to_modify: List[tuple[UCICommand, UCICommand]] = []
        self.remote_only: List[UCICommand] = []  # UCI settings on remote but not mentioned in config
        self.common: List[UCICommand] = []  # UCI settings that match between local and remote

    def is_empty(self) -> bool:
        """Check if there are no differences."""
        return not (self.to_add or self.to_remove or self.to_modify or self.remote_only)

    def _group_commands_by_resource(
        self, commands: List[UCICommand]
    ) -> Dict[str, Dict[str, List[UCICommand]]]:
        """
        Group commands by package and section.

        Returns:
            Dict[package, Dict[section, List[commands]]]
        """
        grouped: Dict[str, Dict[str, List[UCICommand]]] = {}

        for cmd in commands:
            # Parse the path: package.section.option
            parts = cmd.path.split(".")
            if len(parts) < 2:
                continue

            package = parts[0]
            section = parts[1]

            if package not in grouped:
                grouped[package] = {}
            if section not in grouped[package]:
                grouped[package][section] = []

            grouped[package][section].append(cmd)

        return grouped

    def __str__(self) -> str:
        """Format the diff for display."""
        return self.to_string(color=True)

    def to_string(self, color: bool = False) -> str:
        """
        Format the diff for display.

        Args:
            color: If True, use ANSI color codes for terminal output

        Returns:
            Formatted diff string
        """
        if self.is_empty():
            return "No differences found."

        lines = []

        # Color prefixes
        if color:
            add_prefix = f"{Colors.GREEN}+{Colors.RESET}"
            remove_prefix = f"{Colors.RED}-{Colors.RESET}"
            modify_prefix = f"{Colors.YELLOW}~{Colors.RESET}"
            remote_prefix = f"{Colors.CYAN}*{Colors.RESET}"
            bold = f"{Colors.BOLD}"
            reset = f"{Colors.RESET}"
        else:
            add_prefix = "+"
            remove_prefix = "-"
            modify_prefix = "~"
            remote_prefix = "*"
            bold = ""
            reset = ""

        if self.to_add:
            lines.append("Commands to add:")
            for cmd in self.to_add:
                lines.append(f"  {add_prefix} {cmd.to_string()}")

        if self.to_remove:
            lines.append("\nCommands to remove:")
            for cmd in self.to_remove:
                lines.append(f"  {remove_prefix} {cmd.to_string()}")

        if self.to_modify:
            lines.append("\nCommands to modify:")
            for old_cmd, new_cmd in self.to_modify:
                lines.append(f"  {remove_prefix} {old_cmd.to_string()}")
                lines.append(f"  {add_prefix} {new_cmd.to_string()}")

        if self.remote_only:
            lines.append("\nRemote-only settings (not managed by config):")
            for cmd in self.remote_only:
                lines.append(f"  {remote_prefix} {cmd.to_string()}")

        # Summary footer
        summary_parts = []
        if self.to_add:
            summary_parts.append(f"{add_prefix}{len(self.to_add)} to add")
        if self.to_modify:
            summary_parts.append(f"{modify_prefix}{len(self.to_modify)} to modify")
        if self.to_remove:
            summary_parts.append(f"{remove_prefix}{len(self.to_remove)} to remove")
        if self.remote_only:
            summary_parts.append(f"{remote_prefix}{len(self.remote_only)} remote-only")
        if self.common:
            summary_parts.append(f"{len(self.common)} in common")

        if summary_parts:
            lines.append("")
            lines.append(f"{bold}Summary:{reset} {', '.join(summary_parts)}")

        return "\n".join(lines)

    def to_tree(self, color: bool = True) -> str:
        """
        Format the diff as a hierarchical tree grouped by package and resource.

        Args:
            color: If True, use ANSI color codes for terminal output

        Returns:
            A tree-structured string representation of the diff
        """
        if self.is_empty():
            return "No differences found."

        lines = []

        # Color codes
        if color:
            add_sym = f"{Colors.GREEN}+{Colors.RESET}"
            remove_sym = f"{Colors.RED}-{Colors.RESET}"
            modify_sym = f"{Colors.YELLOW}~{Colors.RESET}"
            remote_sym = f"{Colors.CYAN}*{Colors.RESET}"
            pkg_color = f"{Colors.BOLD}"
            reset = f"{Colors.RESET}"
            remote_label = f"{Colors.DIM}(remote-only){Colors.RESET}"
        else:
            add_sym = "+"
            remove_sym = "-"
            modify_sym = "~"
            remote_sym = "*"
            pkg_color = ""
            reset = ""
            remote_label = "(remote-only)"

        # Group all changes by package and section
        add_grouped = self._group_commands_by_resource(self.to_add)
        remove_grouped = self._group_commands_by_resource(self.to_remove)
        remote_only_grouped = self._group_commands_by_resource(self.remote_only)

        # Group modifications
        modify_grouped: Dict[str, Dict[str, List[tuple[UCICommand, UCICommand]]]] = {}
        for old_cmd, new_cmd in self.to_modify:
            parts = new_cmd.path.split(".")
            if len(parts) < 2:
                continue
            package = parts[0]
            section = parts[1]

            if package not in modify_grouped:
                modify_grouped[package] = {}
            if section not in modify_grouped[package]:
                modify_grouped[package][section] = []

            modify_grouped[package][section].append((old_cmd, new_cmd))

        # Get all packages involved
        all_packages = set()
        all_packages.update(add_grouped.keys())
        all_packages.update(remove_grouped.keys())
        all_packages.update(modify_grouped.keys())
        all_packages.update(remote_only_grouped.keys())

        # Format tree for each package
        for package in sorted(all_packages):
            lines.append(f"\n{pkg_color}{package}/{reset}")

            # Get all sections in this package
            sections = set()
            if package in add_grouped:
                sections.update(add_grouped[package].keys())
            if package in remove_grouped:
                sections.update(remove_grouped[package].keys())
            if package in modify_grouped:
                sections.update(modify_grouped[package].keys())
            if package in remote_only_grouped:
                sections.update(remote_only_grouped[package].keys())

            sections_list = sorted(sections)
            for i, section in enumerate(sections_list):
                is_last_section = i == len(sections_list) - 1
                section_prefix = "└── " if is_last_section else "├── "
                item_prefix = "    " if is_last_section else "│   "

                lines.append(f"{section_prefix}{section}")

                # Add commands to add
                if package in add_grouped and section in add_grouped[package]:
                    for cmd in add_grouped[package][section]:
                        option = ".".join(cmd.path.split(".")[2:]) if len(cmd.path.split(".")) > 2 else cmd.path
                        lines.append(f"{item_prefix}  {add_sym} {option} = {cmd.value}")

                # Add commands to remove
                if package in remove_grouped and section in remove_grouped[package]:
                    for cmd in remove_grouped[package][section]:
                        option = ".".join(cmd.path.split(".")[2:]) if len(cmd.path.split(".")) > 2 else cmd.path
                        lines.append(f"{item_prefix}  {remove_sym} {option} = {cmd.value}")

                # Add commands to modify
                if package in modify_grouped and section in modify_grouped[package]:
                    for old_cmd, new_cmd in modify_grouped[package][section]:
                        option = ".".join(new_cmd.path.split(".")[2:]) if len(new_cmd.path.split(".")) > 2 else new_cmd.path
                        lines.append(f"{item_prefix}  {modify_sym} {option}")
                        lines.append(f"{item_prefix}    {remove_sym} {old_cmd.value}")
                        lines.append(f"{item_prefix}    {add_sym} {new_cmd.value}")

                # Add remote-only commands
                if package in remote_only_grouped and section in remote_only_grouped[package]:
                    for cmd in remote_only_grouped[package][section]:
                        option = ".".join(cmd.path.split(".")[2:]) if len(cmd.path.split(".")) > 2 else cmd.path
                        lines.append(f"{item_prefix}  {remote_sym} {option} = {cmd.value} {remote_label}")

        # Summary footer
        summary_parts = []
        if self.to_add:
            summary_parts.append(f"{add_sym}{len(self.to_add)} to add")
        if self.to_modify:
            summary_parts.append(f"{modify_sym}{len(self.to_modify)} to modify")
        if self.to_remove:
            summary_parts.append(f"{remove_sym}{len(self.to_remove)} to remove")
        if self.remote_only:
            summary_parts.append(f"{remote_sym}{len(self.remote_only)} remote-only")
        if self.common:
            summary_parts.append(f"{len(self.common)} in common")

        if summary_parts:
            lines.append("")
            lines.append(f"{pkg_color}Summary:{reset} {', '.join(summary_parts)}")

        return "\n".join(lines)


class UCIConfig:
    """Main UCI configuration class."""

    def __init__(self):
        self.network = NetworkConfig()
        self.wireless = WirelessConfig()
        self.dhcp = DHCPConfig()
        self.firewall = FirewallConfig()

    # Convenience methods to maintain backward compatibility
    def add_network_interface(self, interface: 'NetworkInterface') -> 'UCIConfig':
        """Add a network interface to the configuration."""
        self.network.add_interface(interface)
        return self

    def add_network_device(self, device: 'NetworkDevice') -> 'UCIConfig':
        """Add a network device to the configuration."""
        self.network.add_device(device)
        return self

    def add_wireless_radio(self, radio: 'WirelessRadio') -> 'UCIConfig':
        """Add a wireless radio to the configuration."""
        self.wireless.add_radio(radio)
        return self

    def add_wireless_interface(self, interface: 'WirelessInterface') -> 'UCIConfig':
        """Add a wireless interface to the configuration."""
        self.wireless.add_interface(interface)
        return self

    def add_dhcp_section(self, dhcp: 'DHCPSection') -> 'UCIConfig':
        """Add a DHCP section to the configuration."""
        self.dhcp.add_dhcp(dhcp)
        return self

    def add_firewall_zone(self, zone: 'FirewallZone') -> 'UCIConfig':
        """Add a firewall zone to the configuration."""
        self.firewall.add_zone(zone)
        return self

    def add_firewall_forwarding(self, forwarding: 'FirewallForwarding') -> 'UCIConfig':
        """Add a firewall forwarding rule to the configuration."""
        self.firewall.add_forwarding(forwarding)
        return self

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

    def _parse_uci_export_format(self, package: str, config_str: str) -> List[UCICommand]:
        """Parse UCI export format: package.section.option='value'"""
        commands = []
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
        return commands

    def _parse_uci_show_format(self, package: str, config_str: str) -> List[UCICommand]:
        """
        Parse UCI show format:
        config interface 'loopback'
            option device 'lo'
            option proto 'static'
            list ipaddr '127.0.0.1/8'
        """
        commands = []
        current_section = None

        for line in config_str.strip().split("\n"):
            line = line.rstrip()
            if not line or line.startswith("package "):
                continue

            # Section definition: config <type> '<name>'
            if line.startswith("config "):
                parts = line.split("'")
                if len(parts) >= 2:
                    section_name = parts[1]
                    section_type = line.split()[1].strip("'")
                    current_section = section_name
                    # Add section definition
                    commands.append(UCICommand("set", f"{package}.{section_name}", section_type))

            # Option: \toption <name> '<value>'
            elif line.startswith("\toption ") and current_section:
                parts = line.strip().split("'")
                if len(parts) >= 2:
                    option_name = line.split()[1].strip("'")
                    option_value = parts[1]
                    commands.append(UCICommand("set", f"{package}.{current_section}.{option_name}", option_value))

            # List: \tlist <name> '<value>'
            elif line.startswith("\tlist ") and current_section:
                parts = line.strip().split("'")
                if len(parts) >= 2:
                    list_name = line.split()[1].strip("'")
                    list_value = parts[1]
                    # For lists, we use add_list command
                    commands.append(UCICommand("add_list", f"{package}.{current_section}.{list_name}", list_value))

        return commands

    def _parse_remote_config(self, ssh: SSHConnection) -> List[UCICommand]:
        """
        Parse the remote UCI configuration into commands.

        Handles both 'uci export' and 'uci show' format.
        """
        commands = []
        packages = ["network", "wireless", "dhcp", "firewall"]

        for package in packages:
            try:
                config_str = ssh.get_uci_config(package)

                # Detect format: 'uci export' uses = syntax, 'uci show' uses 'config'/'option' syntax
                if "config " in config_str or "\toption " in config_str:
                    # UCI show format
                    commands.extend(self._parse_uci_show_format(package, config_str))
                else:
                    # UCI export format
                    commands.extend(self._parse_uci_export_format(package, config_str))

            except Exception as e:
                # If we can't get a package, just skip it
                print(f"Warning: Could not retrieve {package} config: {e}")
                continue

        return commands

    def diff(self, ssh: SSHConnection, show_remote_only: bool = True) -> ConfigDiff:
        """
        Compare this configuration with the remote device configuration.

        Args:
            ssh: SSH connection to the remote device
            show_remote_only: If True, track UCI settings on remote but not mentioned in local config

        Returns:
            A ConfigDiff object describing the differences
        """
        local_commands = self.get_all_commands()
        remote_commands = self._parse_remote_config(ssh)

        diff = ConfigDiff()

        # Create sets for comparison
        # For add_list commands, we compare (path, value) pairs
        # For set commands, we track path -> value mapping
        local_set = {(cmd.path, cmd.value) for cmd in local_commands}
        remote_set = {(cmd.path, cmd.value) for cmd in remote_commands}

        # Track paths and their actions (set vs add_list)
        local_paths_by_action = {}  # {path: action}
        for cmd in local_commands:
            if cmd.action == "set":
                local_paths_by_action[cmd.path] = "set"
            # For add_list, don't track as we want per-item comparison

        local_paths = {c.path for c in local_commands}

        # Commands in local but not in remote
        for cmd in local_commands:
            key = (cmd.path, cmd.value)
            if key not in remote_set:
                # For add_list commands, if the (path, value) pair doesn't exist, it's an addition
                if cmd.action == "add_list":
                    diff.to_add.append(cmd)
                else:
                    # For set commands, check if path exists in remote with different value
                    remote_paths = {c.path for c in remote_commands if c.action == "set"}
                    if cmd.path in remote_paths:
                        # Find the remote command with same path
                        remote_cmd = next(c for c in remote_commands if c.path == cmd.path and c.action == "set")
                        diff.to_modify.append((remote_cmd, cmd))
                    else:
                        diff.to_add.append(cmd)
            else:
                # Setting exists in both with same value
                diff.common.append(cmd)

        # Commands in remote but not in local
        for cmd in remote_commands:
            key = (cmd.path, cmd.value)
            if key not in local_set:
                # For add_list commands, if the (path, value) pair doesn't exist locally, it's remote-only
                if cmd.action == "add_list":
                    if show_remote_only:
                        diff.remote_only.append(cmd)
                    else:
                        diff.to_remove.append(cmd)
                else:
                    # For set commands, check if path exists in local
                    if cmd.path not in local_paths:
                        # Path doesn't exist in local config at all
                        if show_remote_only:
                            diff.remote_only.append(cmd)
                        else:
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
