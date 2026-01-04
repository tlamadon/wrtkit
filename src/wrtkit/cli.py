"""Command-line interface for WRTKit device configuration management."""

import sys
import re
from pathlib import Path
from typing import Optional, Union, Any

import click
from dotenv import load_dotenv

from .config import UCIConfig, ConfigDiff, get_display_value
from .ssh import SSHConnection
from .serial_connection import SerialConnection
from .network import NetworkDevice, NetworkInterface
from .wireless import WirelessRadio, WirelessInterface
from .dhcp import DHCPSection
from .firewall import FirewallZone, FirewallForwarding
from .sqm import SQMQueue
from .progress import Spinner
from .fleet import load_fleet, filter_devices, merge_device_configs
from .fleet_executor import FleetExecutor, DeviceResult


def _load_env_files() -> None:
    """Load environment variables from .env files.

    Searches for .env in:
    1. Current working directory
    2. Directory containing the config file (if applicable)
    """
    # Load from current working directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
    else:
        # Try default load_dotenv behavior (searches up directory tree)
        load_dotenv()


# Load environment variables from .env file at startup
_load_env_files()

# Type alias for connection - both implement same interface
Connection = Union[SSHConnection, SerialConnection]


def parse_target(target: str) -> dict[str, Any]:
    """
    Parse a target string into connection parameters.

    Supports:
    - IP address: 192.168.1.1
    - Hostname: router.local
    - IP:port: 192.168.1.1:2222
    - user@host: root@192.168.1.1
    - user@host:port: root@192.168.1.1:2222
    - Serial port: /dev/ttyUSB0 or COM3

    Returns:
        Dictionary with connection parameters
    """
    # Check if it's a serial port
    if target.startswith("/dev/") or target.upper().startswith("COM"):
        return {"type": "serial", "port": target}

    # Parse SSH target
    result = {"type": "ssh", "host": target, "port": 22, "username": "root"}

    # Check for user@host format
    if "@" in target:
        user_part, host_part = target.split("@", 1)
        result["username"] = user_part
        target = host_part

    # Check for host:port format
    if ":" in target:
        # Handle IPv6 addresses in brackets [::1]:port
        if target.startswith("["):
            match = re.match(r"\[([^\]]+)\]:?(\d+)?", target)
            if match:
                result["host"] = match.group(1)
                if match.group(2):
                    result["port"] = int(match.group(2))
        else:
            host, port = target.rsplit(":", 1)
            result["host"] = host
            try:
                result["port"] = int(port)
            except ValueError:
                # Not a valid port, treat the whole thing as hostname
                result["host"] = target
    else:
        result["host"] = target

    return result


def create_connection(
    target: str,
    password: Optional[str] = None,
    key_file: Optional[str] = None,
    timeout: int = 30,
) -> Connection:
    """Create a connection based on target type."""
    params = parse_target(target)

    if params["type"] == "serial":
        return SerialConnection(
            port=params["port"],
            timeout=float(timeout),
            login_username="root",
            login_password=password,
        )
    else:
        return SSHConnection(
            host=params["host"],
            port=params["port"],
            username=params["username"],
            password=password,
            key_filename=key_file,
            timeout=timeout,
        )


def _parse_uci_export_to_dict(package: str, config_str: str) -> dict[str, dict[str, Any]]:
    """Parse UCI export format into a dict of sections.

    Returns:
        Dict mapping section_name -> {type: str, options: dict}
    """
    sections: dict[str, dict[str, Any]] = {}
    current_section: Optional[str] = None
    current_type: Optional[str] = None

    for line in config_str.strip().split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#") or line.startswith("package "):
            continue

        # Section definition: config <type> '<name>'
        if line.startswith("config "):
            parts = line.split("'")
            if len(parts) >= 2:
                current_section = parts[1]
                current_type = line.split()[1].strip("'")
                sections[current_section] = {"_type": current_type}

        # Option: \toption <name> '<value>'
        elif line.startswith("\toption ") and current_section:
            parts = line.strip().split("'")
            if len(parts) >= 2:
                option_name = line.split()[1].strip("'")
                option_value = parts[1]
                # Try to convert to int/bool if applicable
                if option_value.isdigit():
                    sections[current_section][option_name] = int(option_value)
                elif option_value.lower() in ("true", "false"):
                    sections[current_section][option_name] = option_value.lower() == "true"
                else:
                    sections[current_section][option_name] = option_value

        # List: \tlist <name> '<value>'
        elif line.startswith("\tlist ") and current_section:
            parts = line.strip().split("'")
            if len(parts) >= 2:
                list_name = line.split()[1].strip("'")
                list_value = parts[1]
                if list_name not in sections[current_section]:
                    sections[current_section][list_name] = []
                sections[current_section][list_name].append(list_value)

    return sections


def _import_remote_config(conn: Connection) -> UCIConfig:
    """Import configuration from a remote device into a UCIConfig object."""
    config = UCIConfig()
    packages = ["network", "wireless", "dhcp", "firewall", "sqm"]

    for package in packages:
        try:
            config_str = conn.get_uci_config(package)
            sections = _parse_uci_export_to_dict(package, config_str)

            if package == "network":
                for name, opts in sections.items():
                    section_type = opts.pop("_type", "")
                    if section_type == "device":
                        device = NetworkDevice(name, **opts)
                        config.network.add_device(device)
                    elif section_type == "interface":
                        interface = NetworkInterface(name, **opts)
                        config.network.add_interface(interface)

            elif package == "wireless":
                for name, opts in sections.items():
                    section_type = opts.pop("_type", "")
                    if section_type == "wifi-device":
                        radio = WirelessRadio(name, **opts)
                        config.wireless.add_radio(radio)
                    elif section_type == "wifi-iface":
                        iface = WirelessInterface(name, **opts)
                        config.wireless.add_interface(iface)

            elif package == "dhcp":
                for name, opts in sections.items():
                    section_type = opts.pop("_type", "")
                    if section_type == "dhcp":
                        dhcp = DHCPSection(name, **opts)
                        config.dhcp.add_dhcp(dhcp)

            elif package == "firewall":
                zone_idx = 0
                fwd_idx = 0
                for name, opts in sections.items():
                    section_type = opts.pop("_type", "")
                    if section_type == "zone":
                        zone = FirewallZone(zone_idx, **opts)
                        config.firewall.add_zone(zone)
                        zone_idx += 1
                    elif section_type == "forwarding":
                        fwd = FirewallForwarding(fwd_idx, **opts)
                        config.firewall.add_forwarding(fwd)
                        fwd_idx += 1

            elif package == "sqm":
                for name, opts in sections.items():
                    section_type = opts.pop("_type", "")
                    if section_type == "queue":
                        queue = SQMQueue(name, **opts)
                        config.sqm.add_queue(queue)

        except Exception as e:
            click.echo(f"Warning: Could not import {package}: {e}", err=True)
            continue

    return config


def format_commands(diff: ConfigDiff, show_all: bool = False) -> str:
    """Format UCI commands from a diff for display.

    Sensitive values (passwords, keys) are masked for security.
    """
    lines = []

    if diff.to_add:
        lines.append("# Commands to add:")
        for cmd in diff.to_add:
            display_val = get_display_value(cmd.path, cmd.value)
            lines.append(cmd.to_string_with_value(display_val))

    if diff.to_modify:
        lines.append("\n# Commands to modify (new values):")
        for old_cmd, new_cmd in diff.to_modify:
            old_display_val = get_display_value(old_cmd.path, old_cmd.value)
            new_display_val = get_display_value(new_cmd.path, new_cmd.value)
            lines.append(f"# was: {old_cmd.to_string_with_value(old_display_val)}")
            lines.append(new_cmd.to_string_with_value(new_display_val))

    if diff.to_remove:
        lines.append("\n# Commands to remove:")
        for cmd in diff.get_removal_commands():
            display_val = get_display_value(cmd.path, cmd.value) if cmd.value else ""
            lines.append(cmd.to_string_with_value(display_val))

    if show_all and diff.remote_only:
        lines.append("\n# Remote-only settings (not in config):")
        for cmd in diff.remote_only:
            display_val = get_display_value(cmd.path, cmd.value)
            lines.append(f"# {cmd.to_string_with_value(display_val)}")

    return "\n".join(lines)


@click.group()
@click.version_option(version="0.1.0", prog_name="wrtkit")
def cli() -> None:
    """WRTKit - OpenWRT configuration management CLI.

    Manage OpenWRT device configurations using YAML files.
    Connect via SSH (IP/hostname) or serial port (/dev/ttyUSB0).

    Examples:

        \b
        # Preview changes
        wrtkit preview config.yaml 192.168.1.1

        \b
        # Preview with UCI commands
        wrtkit preview config.yaml router.local --show-commands

        \b
        # Apply changes (dry-run first)
        wrtkit apply config.yaml 192.168.1.1 --dry-run

        \b
        # Apply changes for real
        wrtkit apply config.yaml root@192.168.1.1 -p mypassword
    """
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.argument("target", envvar="WRTKIT_TARGET")
@click.option("-p", "--password", envvar="WRTKIT_PASSWORD", help="SSH/login password")
@click.option(
    "-k",
    "--key-file",
    type=click.Path(exists=True),
    envvar="WRTKIT_KEY_FILE",
    help="SSH private key file",
)
@click.option(
    "-t", "--timeout", default=30, envvar="WRTKIT_TIMEOUT", help="Connection timeout in seconds"
)
@click.option("--show-commands", is_flag=True, help="Show UCI commands that would be executed")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--tree", is_flag=True, default=True, help="Show diff as tree (default)")
@click.option("--linear", is_flag=True, help="Show diff as linear list")
def preview(
    config_file: str,
    target: str,
    password: Optional[str],
    key_file: Optional[str],
    timeout: int,
    show_commands: bool,
    no_color: bool,
    tree: bool,
    linear: bool,
) -> None:
    """Preview configuration differences without applying.

    CONFIG_FILE is the path to a YAML or JSON configuration file.
    TARGET is the device to compare against (IP, hostname, or serial port).

    Examples:

        \b
        wrtkit preview config.yaml 192.168.1.1
        wrtkit preview config.yaml router.local --show-commands
        wrtkit preview config.yaml /dev/ttyUSB0 -p password
    """
    try:
        # Load configuration
        if config_file.endswith(".json"):
            config = UCIConfig.from_json_file(config_file)
        else:
            config = UCIConfig.from_yaml_file(config_file)

        click.echo(f"Connecting to {target}...")

        # Connect and compute diff
        conn = create_connection(target, password, key_file, timeout)
        with conn:
            diff = config.diff(conn, show_remote_only=True, verbose=True)  # type: ignore[arg-type]

        # Display results
        if diff.is_empty():
            click.echo("\nConfiguration is in sync - no differences found.")
            return

        click.echo()

        # Show diff in requested format
        use_color = not no_color and sys.stdout.isatty()
        if linear:
            click.echo(diff.to_string(color=use_color))
        else:
            click.echo(diff.to_tree(color=use_color))

        # Show UCI commands if requested
        if show_commands:
            click.echo("\n" + "=" * 60)
            click.echo("UCI Commands:")
            click.echo("=" * 60)
            click.echo(format_commands(diff, show_all=True))

    except FileNotFoundError:
        click.echo(f"Error: Configuration file not found: {config_file}", err=True)
        sys.exit(1)
    except ConnectionError as e:
        click.echo(f"Error: Failed to connect to {target}: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.argument("target", envvar="WRTKIT_TARGET")
@click.option("-p", "--password", envvar="WRTKIT_PASSWORD", help="SSH/login password")
@click.option(
    "-k",
    "--key-file",
    type=click.Path(exists=True),
    envvar="WRTKIT_KEY_FILE",
    help="SSH private key file",
)
@click.option(
    "-t", "--timeout", default=30, envvar="WRTKIT_TIMEOUT", help="Connection timeout in seconds"
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--show-commands", is_flag=True, help="Show UCI commands that would be executed")
@click.option("--no-commit", is_flag=True, help="Don't commit changes after applying")
@click.option("--no-reload", is_flag=True, help="Don't reload services after applying")
@click.option(
    "--remove-unmanaged",
    is_flag=True,
    help="Remove settings on device that are not in config (dangerous!)",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt")
def apply(
    config_file: str,
    target: str,
    password: Optional[str],
    key_file: Optional[str],
    timeout: int,
    dry_run: bool,
    show_commands: bool,
    no_commit: bool,
    no_reload: bool,
    remove_unmanaged: bool,
    no_color: bool,
    yes: bool,
) -> None:
    """Apply configuration to a device.

    CONFIG_FILE is the path to a YAML or JSON configuration file.
    TARGET is the device to configure (IP, hostname, or serial port).

    Examples:

        \b
        # Dry run first
        wrtkit apply config.yaml 192.168.1.1 --dry-run

        \b
        # Apply with confirmation
        wrtkit apply config.yaml 192.168.1.1 -p password

        \b
        # Apply without prompting
        wrtkit apply config.yaml router.local -y

        \b
        # Show commands during dry-run
        wrtkit apply config.yaml 192.168.1.1 --dry-run --show-commands
    """
    try:
        # Load configuration
        if config_file.endswith(".json"):
            config = UCIConfig.from_json_file(config_file)
        else:
            config = UCIConfig.from_yaml_file(config_file)

        click.echo(f"Connecting to {target}...")

        # Connect and compute diff
        conn = create_connection(target, password, key_file, timeout)
        with conn:
            # First get the diff to show what will be done
            diff = config.diff(
                conn,  # type: ignore[arg-type]
                show_remote_only=not remove_unmanaged,
                verbose=True,
            )

            if diff.is_empty() and not diff.to_remove:
                click.echo("\nConfiguration is already in sync - nothing to apply.")
                return

            # Show the diff
            use_color = not no_color and sys.stdout.isatty()
            click.echo()
            click.echo(diff.to_tree(color=use_color))

            # Show UCI commands if requested
            if show_commands:
                click.echo("\n" + "=" * 60)
                click.echo("UCI Commands to execute:")
                click.echo("=" * 60)
                click.echo(format_commands(diff))

            if dry_run:
                click.echo("\n[Dry run mode - no changes made]")

                # Also show what commit/reload would happen
                if not no_commit:
                    click.echo("Would run: uci commit")
                if not no_reload:
                    click.echo("Would run: /etc/init.d/network restart")
                    click.echo("Would run: wifi reload")
                    click.echo("Would run: /etc/init.d/dnsmasq restart")
                return

            # Confirmation prompt
            if not yes:
                changes_count = len(diff.to_add) + len(diff.to_modify) + len(diff.to_remove)
                click.echo()
                if not click.confirm(f"Apply {changes_count} changes to {target}?"):
                    click.echo("Aborted.")
                    return

            # Apply the configuration
            click.echo()
            diff = config.apply_diff(
                conn,  # type: ignore[arg-type]
                remove_unmanaged=remove_unmanaged,
                dry_run=False,
                auto_commit=not no_commit,
                auto_reload=not no_reload,
                verbose=True,
            )

            click.echo("\nConfiguration applied successfully!")

    except FileNotFoundError:
        click.echo(f"Error: Configuration file not found: {config_file}", err=True)
        sys.exit(1)
    except ConnectionError as e:
        click.echo(f"Error: Failed to connect to {target}: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--no-color", is_flag=True, help="Disable colored output")
def validate(config_file: str, no_color: bool) -> None:
    """Validate a configuration file without connecting to a device.

    CONFIG_FILE is the path to a YAML or JSON configuration file.

    Examples:

        \b
        wrtkit validate config.yaml
        wrtkit validate network.json
    """
    try:
        # Load configuration
        if config_file.endswith(".json"):
            config = UCIConfig.from_json_file(config_file)
        else:
            config = UCIConfig.from_yaml_file(config_file)

        # Get all commands to verify the config is valid
        commands = config.get_all_commands()

        click.echo("Configuration is valid!")
        click.echo(f"  - Network devices: {len(config.network.devices)}")
        click.echo(f"  - Network interfaces: {len(config.network.interfaces)}")
        click.echo(f"  - Wireless radios: {len(config.wireless.radios)}")
        click.echo(f"  - Wireless interfaces: {len(config.wireless.interfaces)}")
        click.echo(f"  - DHCP sections: {len(config.dhcp.sections)}")
        click.echo(f"  - Firewall zones: {len(config.firewall.zones)}")
        click.echo(f"  - Firewall forwardings: {len(config.firewall.forwardings)}")
        click.echo(f"  - SQM queues: {len(config.sqm.queues)}")
        click.echo(f"  - Total UCI commands: {len(commands)}")

    except FileNotFoundError:
        click.echo(f"Error: Configuration file not found: {config_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: Invalid configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def commands(config_file: str) -> None:
    """Show all UCI commands from a configuration file.

    CONFIG_FILE is the path to a YAML or JSON configuration file.

    Examples:

        \b
        wrtkit commands config.yaml
        wrtkit commands config.yaml > apply.sh
    """
    try:
        # Load configuration
        if config_file.endswith(".json"):
            config = UCIConfig.from_json_file(config_file)
        else:
            config = UCIConfig.from_yaml_file(config_file)

        # Output as shell script
        click.echo(config.to_script(include_commit=True, include_reload=True))

    except FileNotFoundError:
        click.echo(f"Error: Configuration file not found: {config_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("import")
@click.argument("target", envvar="WRTKIT_TARGET")
@click.argument("output_file", type=click.Path())
@click.option("-p", "--password", envvar="WRTKIT_PASSWORD", help="SSH/login password")
@click.option(
    "-k",
    "--key-file",
    type=click.Path(exists=True),
    envvar="WRTKIT_KEY_FILE",
    help="SSH private key file",
)
@click.option(
    "-t", "--timeout", default=30, envvar="WRTKIT_TIMEOUT", help="Connection timeout in seconds"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default=None,
    help="Output format (auto-detected from file extension if not specified)",
)
@click.option(
    "--packages",
    default="network,wireless,dhcp,firewall,sqm",
    help="Comma-separated list of UCI packages to import (default: all)",
)
def import_config(
    target: str,
    output_file: str,
    password: Optional[str],
    key_file: Optional[str],
    timeout: int,
    output_format: Optional[str],
    packages: str,
) -> None:
    """Import configuration from a device and save as YAML/JSON.

    Connects to a remote device, reads its UCI configuration, and saves
    it in wrtkit's YAML/JSON format. The resulting file can be used with
    'wrtkit apply' to configure other routers.

    TARGET is the device to import from (IP, hostname, or serial port).
    OUTPUT_FILE is where to save the configuration (.yaml or .json).

    Examples:

        \b
        # Import full config from router
        wrtkit import 192.168.1.1 router-backup.yaml

        \b
        # Import as JSON
        wrtkit import router.local config.json

        \b
        # Import only network and wireless
        wrtkit import 192.168.1.1 minimal.yaml --packages network,wireless

        \b
        # Use imported config on another router
        wrtkit apply router-backup.yaml 192.168.1.2
    """
    try:
        # Determine output format
        if output_format is None:
            if output_file.endswith(".json"):
                output_format = "json"
            else:
                output_format = "yaml"

        click.echo(f"Connecting to {target}...")

        # Connect and import config
        conn = create_connection(target, password, key_file, timeout)

        with conn:
            spinner = Spinner("Importing configuration...")
            spinner.start()

            try:
                config = UCIConfig()
                package_list = [p.strip() for p in packages.split(",")]

                for package in package_list:
                    spinner.update(f"Importing {package}...")
                    try:
                        config_str = conn.get_uci_config(package)
                        sections = _parse_uci_export_to_dict(package, config_str)

                        if package == "network":
                            for name, opts in sections.items():
                                section_type = opts.pop("_type", "")
                                if section_type == "device":
                                    device = NetworkDevice(name, **opts)
                                    config.network.add_device(device)
                                elif section_type == "interface":
                                    interface = NetworkInterface(name, **opts)
                                    config.network.add_interface(interface)

                        elif package == "wireless":
                            for name, opts in sections.items():
                                section_type = opts.pop("_type", "")
                                if section_type == "wifi-device":
                                    radio = WirelessRadio(name, **opts)
                                    config.wireless.add_radio(radio)
                                elif section_type == "wifi-iface":
                                    iface = WirelessInterface(name, **opts)
                                    config.wireless.add_interface(iface)

                        elif package == "dhcp":
                            for name, opts in sections.items():
                                section_type = opts.pop("_type", "")
                                if section_type == "dhcp":
                                    dhcp = DHCPSection(name, **opts)
                                    config.dhcp.add_dhcp(dhcp)

                        elif package == "firewall":
                            zone_idx = 0
                            fwd_idx = 0
                            for name, opts in sections.items():
                                section_type = opts.pop("_type", "")
                                if section_type == "zone":
                                    zone = FirewallZone(zone_idx, **opts)
                                    config.firewall.add_zone(zone)
                                    zone_idx += 1
                                elif section_type == "forwarding":
                                    fwd = FirewallForwarding(fwd_idx, **opts)
                                    config.firewall.add_forwarding(fwd)
                                    fwd_idx += 1

                        elif package == "sqm":
                            for name, opts in sections.items():
                                section_type = opts.pop("_type", "")
                                if section_type == "queue":
                                    queue = SQMQueue(name, **opts)
                                    config.sqm.add_queue(queue)

                    except Exception as e:
                        spinner.update(f"Warning: {package} - {e}")
                        continue

                spinner.stop("Configuration imported")

            except Exception as e:
                spinner.stop(f"Failed: {e}")
                raise

        # Save to file
        if output_format == "json":
            config.to_json_file(output_file)
        else:
            config.to_yaml_file(output_file)

        click.echo(f"\nConfiguration saved to {output_file}")
        click.echo(f"  - Network devices: {len(config.network.devices)}")
        click.echo(f"  - Network interfaces: {len(config.network.interfaces)}")
        click.echo(f"  - Wireless radios: {len(config.wireless.radios)}")
        click.echo(f"  - Wireless interfaces: {len(config.wireless.interfaces)}")
        click.echo(f"  - DHCP sections: {len(config.dhcp.sections)}")
        click.echo(f"  - Firewall zones: {len(config.firewall.zones)}")
        click.echo(f"  - Firewall forwardings: {len(config.firewall.forwardings)}")
        click.echo(f"  - SQM queues: {len(config.sqm.queues)}")
        click.echo(f"\nYou can now use this file with 'wrtkit apply {output_file} <target>'")

    except ConnectionError as e:
        click.echo(f"Error: Failed to connect to {target}: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# Fleet Commands
# =============================================================================


@cli.group()
def fleet() -> None:
    """Manage multiple OpenWRT devices from an inventory file.

    Fleet mode enables coordinated configuration updates across multiple devices
    with two-phase execution for safe network changes.

    \b
    Example fleet.yaml:
        defaults:
          timeout: 30
          username: root
          commit_delay: 10

        config_layers:
          base: configs/base.yaml

        devices:
          router:
            target: 192.168.1.1
            password: ${oc.env:ROUTER_PASSWORD}
            configs:
              - ${config_layers.base}
              - configs/router.yaml
            tags: [core, production]
    """
    pass


def _parse_tags(tags_str: Optional[str]) -> Optional[list[str]]:
    """Parse comma-separated tags string into list."""
    if tags_str is None:
        return None
    return [t.strip() for t in tags_str.split(",") if t.strip()]


def _print_fleet_header(
    fleet_file: str, devices: dict, target: Optional[str], tags: Optional[str]
) -> None:
    """Print fleet operation header."""
    click.echo(f"\nFleet: {fleet_file}")
    filter_parts = []
    if target:
        filter_parts.append(f"target: {target}")
    if tags:
        filter_parts.append(f"tags: {tags}")
    if filter_parts:
        click.echo(f"Targets: {len(devices)} device(s) (filtered by {', '.join(filter_parts)})")
    else:
        click.echo(f"Targets: {len(devices)} device(s)")
    click.echo()


@fleet.command("apply")
@click.argument("fleet_file", type=click.Path(exists=True))
@click.option("--target", "-t", help="Device name or glob pattern (e.g., 'ap-*')")
@click.option("--tags", help="Comma-separated tags to filter by (AND logic)")
@click.option("--commit-delay", type=int, help="Seconds to wait before coordinated commit")
@click.option("--remove-unmanaged", is_flag=True, help="Remove settings not in config")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt")
@click.option("--no-color", is_flag=True, help="Disable colored output")
def fleet_apply(
    fleet_file: str,
    target: Optional[str],
    tags: Optional[str],
    commit_delay: Optional[int],
    remove_unmanaged: bool,
    dry_run: bool,
    yes: bool,
    no_color: bool,
) -> None:
    """Apply configuration to fleet devices with coordinated updates.

    Uses two-phase execution for safe network changes:

    \b
    Phase 1 (Stage): Push UCI commands to all devices in parallel.
                     Fails fast if any device fails, rolling back all changes.
    Phase 2 (Commit): Send coordinated commit commands to all devices.
                     All devices restart services at roughly the same time.

    Examples:

        \b
        # Apply to all devices
        wrtkit fleet apply fleet.yaml

        \b
        # Apply to specific device
        wrtkit fleet apply fleet.yaml --target main-router

        \b
        # Apply to devices matching glob
        wrtkit fleet apply fleet.yaml --target "ap-*"

        \b
        # Apply to devices with specific tags
        wrtkit fleet apply fleet.yaml --tags production

        \b
        # Dry run
        wrtkit fleet apply fleet.yaml --dry-run
    """
    try:
        fleet_path = Path(fleet_file)
        fleet_config = load_fleet(fleet_file)

        # Filter devices
        tags_list = _parse_tags(tags)
        devices = filter_devices(fleet_config, target, tags_list)

        if not devices:
            click.echo("No devices matched the specified filters.", err=True)
            sys.exit(1)

        _print_fleet_header(fleet_file, devices, target, tags)

        # Create executor with progress callbacks
        use_color = not no_color and sys.stdout.isatty()

        def on_device_start(name: str, device_target: str) -> None:
            click.echo(f"  {name} ({device_target})...", nl=False)

        def on_device_complete(name: str, result: DeviceResult) -> None:
            if result.success:
                if use_color:
                    click.echo(f" \033[32m✓\033[0m {result.changes_count} changes")
                else:
                    click.echo(f" OK - {result.changes_count} changes")
            else:
                if use_color:
                    click.echo(f" \033[31m✗\033[0m {result.error}")
                else:
                    click.echo(f" FAILED - {result.error}")

        def on_phase_start(phase: str) -> None:
            if phase == "stage":
                click.echo("[Phase 1: Staging Changes]")
            elif phase == "commit":
                delay = commit_delay or fleet_config.defaults.commit_delay
                click.echo(f"\n[Phase 2: Coordinated Commit (delay: {delay}s)]")

        executor = FleetExecutor(
            fleet=fleet_config,
            fleet_path=fleet_path,
            on_device_start=on_device_start,
            on_device_complete=on_device_complete,
            on_phase_start=on_phase_start,
        )

        try:
            if dry_run:
                # Just preview changes
                click.echo("[Dry Run - Preview Mode]")
                result = executor.preview(target=target, tags=tags_list)

                for name, device_result in result.devices.items():
                    click.echo(f"\n{name} ({device_result.target}):")
                    if device_result.success and device_result.diff:
                        if device_result.diff.is_empty():
                            click.echo("  No changes needed")
                        else:
                            click.echo(device_result.diff.to_tree(color=use_color))
                    elif not device_result.success:
                        click.echo(f"  Error: {device_result.error}")

                click.echo("\n[Dry run mode - no changes made]")
                return

            # Confirmation prompt
            if not yes:
                click.echo(f"This will apply changes to {len(devices)} device(s).")
                if not click.confirm("Continue?"):
                    click.echo("Aborted.")
                    return

            # Execute two-phase apply
            stage_result, commit_result = executor.apply(
                target=target,
                tags=tags_list,
                remove_unmanaged=remove_unmanaged,
                commit_delay=commit_delay,
            )

            # Report results
            click.echo()
            if stage_result.aborted:
                if use_color:
                    click.echo(f"\033[31mFleet apply ABORTED:\033[0m {stage_result.abort_reason}")
                else:
                    click.echo(f"Fleet apply ABORTED: {stage_result.abort_reason}")
                click.echo("All staged changes have been rolled back.")
                sys.exit(1)

            if commit_result.all_successful:
                if use_color:
                    click.echo(
                        f"\033[32mFleet apply completed:\033[0m {commit_result.success_count}/{commit_result.total_count} devices updated"
                    )
                else:
                    click.echo(
                        f"Fleet apply completed: {commit_result.success_count}/{commit_result.total_count} devices updated"
                    )
            else:
                if use_color:
                    click.echo(
                        f"\033[33mFleet apply partial:\033[0m {commit_result.success_count}/{commit_result.total_count} devices updated"
                    )
                else:
                    click.echo(
                        f"Fleet apply partial: {commit_result.success_count}/{commit_result.total_count} devices updated"
                    )

                for name, dev_result in commit_result.devices.items():
                    if not dev_result.success:
                        click.echo(f"  - {name}: {dev_result.error}", err=True)
                sys.exit(1)

        finally:
            executor.cleanup()

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@fleet.command("preview")
@click.argument("fleet_file", type=click.Path(exists=True))
@click.option("--target", "-t", help="Device name or glob pattern (e.g., 'ap-*')")
@click.option("--tags", help="Comma-separated tags to filter by (AND logic)")
@click.option("--no-color", is_flag=True, help="Disable colored output")
def fleet_preview(
    fleet_file: str,
    target: Optional[str],
    tags: Optional[str],
    no_color: bool,
) -> None:
    """Preview configuration changes for fleet devices.

    Connects to each device and shows the diff between current and desired config.

    Examples:

        \b
        # Preview all devices
        wrtkit fleet preview fleet.yaml

        \b
        # Preview specific device
        wrtkit fleet preview fleet.yaml --target main-router
    """
    try:
        fleet_path = Path(fleet_file)
        fleet_config = load_fleet(fleet_file)

        tags_list = _parse_tags(tags)
        devices = filter_devices(fleet_config, target, tags_list)

        if not devices:
            click.echo("No devices matched the specified filters.", err=True)
            sys.exit(1)

        _print_fleet_header(fleet_file, devices, target, tags)

        use_color = not no_color and sys.stdout.isatty()

        executor = FleetExecutor(fleet=fleet_config, fleet_path=fleet_path)

        try:
            result = executor.preview(target=target, tags=tags_list)

            total_changes = 0
            for name, device_result in result.devices.items():
                click.echo(f"{name} ({device_result.target}):")
                if device_result.success and device_result.diff:
                    if device_result.diff.is_empty():
                        click.echo("  No changes needed\n")
                    else:
                        click.echo(device_result.diff.to_tree(color=use_color))
                        total_changes += device_result.changes_count
                        click.echo()
                elif not device_result.success:
                    if use_color:
                        click.echo(f"  \033[31mError:\033[0m {device_result.error}\n")
                    else:
                        click.echo(f"  Error: {device_result.error}\n")

            click.echo(
                f"Total: {result.success_count}/{result.total_count} devices scanned, {total_changes} changes pending"
            )

        finally:
            executor.cleanup()

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@fleet.command("validate")
@click.argument("fleet_file", type=click.Path(exists=True))
def fleet_validate(fleet_file: str) -> None:
    """Validate fleet file and all referenced configurations.

    Checks:
    - Fleet file syntax and schema
    - All referenced config files exist
    - Config files are valid YAML/JSON

    Example:

        wrtkit fleet validate fleet.yaml
    """
    try:
        fleet_path = Path(fleet_file)
        fleet_config = load_fleet(fleet_file)

        click.echo(f"Fleet file: {fleet_file}")
        click.echo("  Defaults:")
        click.echo(f"    timeout: {fleet_config.defaults.timeout}s")
        click.echo(f"    username: {fleet_config.defaults.username}")
        click.echo(f"    commit_delay: {fleet_config.defaults.commit_delay}s")

        if fleet_config.config_layers:
            click.echo(f"  Config layers: {len(fleet_config.config_layers)}")
            for name, path in fleet_config.config_layers.items():
                full_path = fleet_path.parent / path if not Path(path).is_absolute() else Path(path)
                exists = "✓" if full_path.exists() else "✗ NOT FOUND"
                click.echo(f"    - {name}: {path} [{exists}]")

        click.echo(f"  Devices: {len(fleet_config.devices)}")

        errors = []
        for name, device in fleet_config.devices.items():
            click.echo(f"\n  {name}:")
            click.echo(f"    target: {device.target}")
            click.echo(f"    tags: {device.tags}")
            click.echo(f"    configs ({len(device.configs)}):")

            for config_path in device.configs:
                full_path = (
                    fleet_path.parent / config_path
                    if not Path(config_path).is_absolute()
                    else Path(config_path)
                )
                if full_path.exists():
                    try:
                        # Try to load and validate
                        merge_device_configs(device, fleet_path)
                        click.echo(f"      - {config_path} [✓]")
                    except Exception as e:
                        click.echo(f"      - {config_path} [✗ {e}]")
                        errors.append(f"{name}: {config_path} - {e}")
                else:
                    click.echo(f"      - {config_path} [✗ NOT FOUND]")
                    errors.append(f"{name}: {config_path} - file not found")

        click.echo()
        if errors:
            click.echo(f"Validation FAILED with {len(errors)} error(s):", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        else:
            click.echo("Validation passed!")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@fleet.command("show")
@click.argument("fleet_file", type=click.Path(exists=True))
@click.option("--target", "-t", required=True, help="Device name to show merged config for")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
def fleet_show(
    fleet_file: str,
    target: str,
    output_format: str,
) -> None:
    """Show merged configuration for a specific device.

    Displays the final configuration after merging all config layers.

    Example:

        wrtkit fleet show fleet.yaml --target main-router
    """
    try:
        fleet_path = Path(fleet_file)
        fleet_config = load_fleet(fleet_file)

        if target not in fleet_config.devices:
            click.echo(f"Error: Device '{target}' not found in fleet", err=True)
            sys.exit(1)

        device = fleet_config.devices[target]
        config = merge_device_configs(device, fleet_path)

        click.echo(f"# Merged configuration for: {target}")
        click.echo(f"# Target: {device.target}")
        click.echo(f"# Config layers: {device.configs}")
        click.echo()

        if output_format == "json":
            click.echo(config.to_json())
        else:
            click.echo(config.to_yaml())

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# Testing Commands
# =============================================================================


@cli.group()
def testing() -> None:
    """Run network tests on OpenWRT devices.

    Testing mode enables running network diagnostics (ping, iperf) between
    devices defined in a fleet inventory.

    \b
    Example test-config.yaml:
        fleet_file: fleet.yaml

        tests:
          - name: ping-router-to-ap
            type: ping
            source: main-router
            destination: ap-living
            count: 10

          - name: iperf-router-to-ap
            type: iperf
            server: ap-living
            client: main-router
            duration: 10
    """
    pass


@testing.command("run")
@click.argument("test_file", type=click.Path(exists=True))
@click.option("--test", "-t", "test_name", help="Run only the specified test by name")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
def testing_run(
    test_file: str,
    test_name: Optional[str],
    no_color: bool,
    output_json: bool,
) -> None:
    """Run network tests from a test configuration file.

    TEST_FILE is the path to a YAML test configuration file.

    Examples:

        \b
        # Run all tests
        wrtkit testing run tests.yaml

        \b
        # Run a specific test
        wrtkit testing run tests.yaml --test ping-router-to-ap

        \b
        # Output as JSON
        wrtkit testing run tests.yaml --json
    """
    from .testing import load_test_config, resolve_tests
    from .test_executor import (
        TestExecutor,
        format_result,
        PingResult,
        IperfResult,
    )
    import json as json_module

    try:
        test_path = Path(test_file)
        test_config = load_test_config(test_file)

        # Resolve tests with fleet device information
        resolved_tests = resolve_tests(test_config, test_path)

        # Filter to specific test if requested
        if test_name:
            resolved_tests = [t for t in resolved_tests if t.name == test_name]
            if not resolved_tests:
                click.echo(f"Error: Test '{test_name}' not found in config", err=True)
                sys.exit(1)

        if not resolved_tests:
            click.echo("No tests defined in configuration.", err=True)
            sys.exit(1)

        use_color = not no_color and sys.stdout.isatty() and not output_json

        if not output_json:
            click.echo(f"Running {len(resolved_tests)} test(s)...\n")

        # Set up callbacks for progress
        def on_test_start(name: str) -> None:
            if not output_json:
                click.echo(f"Running: {name}")

        def on_status(message: str) -> None:
            if not output_json:
                click.echo(f"  {message}")

        # Create executor and run tests
        executor = TestExecutor(
            on_test_start=on_test_start,
            on_status=on_status,
        )

        results = executor.run_tests(resolved_tests)

        # Output results
        if output_json:
            json_results = []
            for r in results:
                if isinstance(r, PingResult):
                    json_results.append(
                        {
                            "name": r.name,
                            "type": "ping",
                            "source": r.source,
                            "destination": r.destination,
                            "packets_sent": r.packets_sent,
                            "packets_received": r.packets_received,
                            "packet_loss_pct": r.packet_loss_pct,
                            "rtt_min": r.rtt_min,
                            "rtt_avg": r.rtt_avg,
                            "rtt_max": r.rtt_max,
                            "success": r.success,
                            "error": r.error,
                        }
                    )
                elif isinstance(r, IperfResult):
                    json_results.append(
                        {
                            "name": r.name,
                            "type": "iperf",
                            "server": r.server,
                            "client": r.client,
                            "protocol": r.protocol,
                            "duration": r.duration,
                            "sent_bytes": r.sent_bytes,
                            "sent_bps": r.sent_bps,
                            "received_bytes": r.received_bytes,
                            "received_bps": r.received_bps,
                            "retransmits": r.retransmits,
                            "jitter_ms": r.jitter_ms,
                            "lost_packets": r.lost_packets,
                            "lost_percent": r.lost_percent,
                            "success": r.success,
                            "error": r.error,
                        }
                    )
            click.echo(json_module.dumps(json_results, indent=2))
        else:
            click.echo("\n" + "=" * 60)
            click.echo("Results")
            click.echo("=" * 60 + "\n")

            for result in results:
                click.echo(format_result(result, use_color))
                click.echo()

            # Summary
            passed = sum(1 for r in results if r.success)
            failed = len(results) - passed

            if use_color:
                if failed == 0:
                    click.echo(f"\033[32mAll {passed} test(s) passed\033[0m")
                else:
                    click.echo(f"\033[31m{failed} test(s) failed\033[0m, {passed} passed")
            else:
                if failed == 0:
                    click.echo(f"All {passed} test(s) passed")
                else:
                    click.echo(f"{failed} test(s) failed, {passed} passed")

        # Exit with error code if any tests failed
        if any(not r.success for r in results):
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@testing.command("validate")
@click.argument("test_file", type=click.Path(exists=True))
def testing_validate(test_file: str) -> None:
    """Validate a test configuration file.

    Checks that:
    - The test file is valid YAML
    - All referenced devices exist in the fleet file
    - Test definitions have required fields

    Examples:

        \b
        wrtkit testing validate tests.yaml
    """
    from .testing import load_test_config, resolve_tests, ResolvedPingTest

    try:
        test_path = Path(test_file)
        test_config = load_test_config(test_file)

        click.echo(f"Test config: {test_file}")
        click.echo(f"Fleet file: {test_config.fleet_file}")
        click.echo(f"Tests defined: {len(test_config.tests)}")
        click.echo()

        # Try to resolve all tests (validates device references)
        resolved = resolve_tests(test_config, test_path)

        click.echo("Tests:")
        for test in resolved:
            if isinstance(test, ResolvedPingTest):
                # Ping test
                click.echo(f"  - {test.name} (ping): {test.source_device} → {test.destination}")
            else:
                # Iperf test
                click.echo(f"  - {test.name} (iperf): {test.client_device} → {test.server_device}")

        click.echo()
        click.echo("✓ Configuration is valid")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Validation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@testing.command("show")
@click.argument("test_file", type=click.Path(exists=True))
@click.option(
    "--format", "-f", "output_format", type=click.Choice(["yaml", "json"]), default="yaml"
)
def testing_show(test_file: str, output_format: str) -> None:
    """Show resolved test configuration.

    Displays the test configuration with all device references resolved
    to their actual targets/IPs.

    Examples:

        \b
        wrtkit testing show tests.yaml
        wrtkit testing show tests.yaml --format json
    """
    from .testing import load_test_config, resolve_tests
    import json as json_module
    import yaml

    try:
        test_path = Path(test_file)
        test_config = load_test_config(test_file)
        resolved = resolve_tests(test_config, test_path)

        # Convert to serializable format
        tests_data = []
        for test in resolved:
            tests_data.append(test.model_dump())

        output_data = {
            "fleet_file": test_config.fleet_file,
            "tests": tests_data,
        }

        if output_format == "json":
            click.echo(json_module.dumps(output_data, indent=2))
        else:
            click.echo(yaml.dump(output_data, default_flow_style=False, sort_keys=False))

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
