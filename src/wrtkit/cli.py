"""Command-line interface for WRTKit device configuration management."""

import sys
import re
from pathlib import Path
from typing import Optional, Union, Any

import click
from dotenv import load_dotenv

from .config import UCIConfig, ConfigDiff
from .ssh import SSHConnection
from .serial_connection import SerialConnection


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


def format_commands(diff: ConfigDiff, show_all: bool = False) -> str:
    """Format UCI commands from a diff for display."""
    lines = []

    if diff.to_add:
        lines.append("# Commands to add:")
        for cmd in diff.to_add:
            lines.append(cmd.to_string())

    if diff.to_modify:
        lines.append("\n# Commands to modify (new values):")
        for old_cmd, new_cmd in diff.to_modify:
            lines.append(f"# was: {old_cmd.to_string()}")
            lines.append(new_cmd.to_string())

    if diff.to_remove:
        lines.append("\n# Commands to remove:")
        for cmd in diff.get_removal_commands():
            lines.append(cmd.to_string())

    if show_all and diff.remote_only:
        lines.append("\n# Remote-only settings (not in config):")
        for cmd in diff.remote_only:
            lines.append(f"# {cmd.to_string()}")

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
    "-k", "--key-file", type=click.Path(exists=True), envvar="WRTKIT_KEY_FILE",
    help="SSH private key file"
)
@click.option("-t", "--timeout", default=30, envvar="WRTKIT_TIMEOUT", help="Connection timeout in seconds")
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
    "-k", "--key-file", type=click.Path(exists=True), envvar="WRTKIT_KEY_FILE",
    help="SSH private key file"
)
@click.option("-t", "--timeout", default=30, envvar="WRTKIT_TIMEOUT", help="Connection timeout in seconds")
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


@cli.command()
@click.argument("target", envvar="WRTKIT_TARGET")
@click.argument("output_file", type=click.Path())
@click.option("-p", "--password", envvar="WRTKIT_PASSWORD", help="SSH/login password")
@click.option(
    "-k", "--key-file", type=click.Path(exists=True), envvar="WRTKIT_KEY_FILE",
    help="SSH private key file"
)
@click.option("-t", "--timeout", default=30, envvar="WRTKIT_TIMEOUT", help="Connection timeout in seconds")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format (default: yaml)",
)
def fetch(
    target: str,
    output_file: str,
    password: Optional[str],
    key_file: Optional[str],
    timeout: int,
    output_format: str,
) -> None:
    """Fetch current configuration from a device and save to file.

    TARGET is the device to fetch from (IP, hostname, or serial port).
    OUTPUT_FILE is where to save the configuration.

    Note: This fetches raw UCI data and converts it to wrtkit format.
    Some manual adjustments may be needed.

    Examples:

        \b
        wrtkit fetch 192.168.1.1 current.yaml
        wrtkit fetch router.local backup.json --format json
    """
    click.echo("Note: fetch command is not yet implemented.")
    click.echo("Use 'wrtkit preview' to see current device configuration.")
    sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
