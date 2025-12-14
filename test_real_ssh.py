#!/usr/bin/env python3
"""
Test script to debug real SSH connection issues.
Use this to test connectivity to your actual OpenWRT device.
"""

from wrtkit import UCIConfig, SSHConnection


def test_ssh_connection():
    """Test SSH connection and remote config retrieval."""

    print("=" * 60)
    print("SSH CONNECTION TEST")
    print("=" * 60)

    # Replace these with your actual device credentials
    host = input("Enter OpenWRT device IP (e.g., 192.168.1.1): ").strip()
    username = input("Enter username (default: root): ").strip() or "root"
    password = input("Enter password: ").strip()

    print(f"\nConnecting to {username}@{host}...")

    try:
        ssh = SSHConnection(host=host, username=username, password=password)
        print("✓ SSH connection successful!\n")

        # Test getting UCI config for each package
        packages = ["network", "wireless", "dhcp", "firewall"]

        for package in packages:
            print(f"\nTesting {package} package:")
            print("-" * 40)
            try:
                config_str = ssh.get_uci_config(package)
                lines = config_str.strip().split("\n")
                print(f"  Retrieved {len(lines)} lines")
                print(f"  First 3 lines:")
                for line in lines[:3]:
                    print(f"    {line}")

                if not config_str.strip():
                    print("  ⚠️  WARNING: Empty config returned!")

            except Exception as e:
                print(f"  ✗ Error: {e}")

        # Test the diff
        print("\n" + "=" * 60)
        print("TESTING DIFF WITH EMPTY CONFIG")
        print("=" * 60)

        config = UCIConfig()
        diff = config.diff(ssh, show_remote_only=True)

        print(f"\nCommands to add: {len(diff.to_add)}")
        print(f"Commands to modify: {len(diff.to_modify)}")
        print(f"Commands to remove: {len(diff.to_remove)}")
        print(f"Remote-only commands: {len(diff.remote_only)}")

        if diff.remote_only:
            print("\n✓ Remote-only detection working!")
            print(f"\nShowing first 5 remote-only settings:")
            for cmd in diff.remote_only[:5]:
                print(f"  * {cmd.to_string()}")
        else:
            print("\n⚠️  No remote-only settings detected.")
            print("This could mean:")
            print("  1. The device has no configuration")
            print("  2. SSH commands are failing silently")
            print("  3. The parser is having issues")

        # Show tree format
        if not diff.is_empty():
            print("\n" + "=" * 60)
            print("TREE FORMAT PREVIEW")
            print("=" * 60)
            tree = diff.to_tree()
            # Show first 30 lines
            tree_lines = tree.split("\n")
            for line in tree_lines[:30]:
                print(line)
            if len(tree_lines) > 30:
                print(f"... ({len(tree_lines) - 30} more lines)")

        ssh.close()
        print("\n✓ Connection closed")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ssh_connection()
