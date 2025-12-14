#!/usr/bin/env python3
"""
Example of using WRTKit with a serial console connection.

This demonstrates how to manage OpenWRT configuration via serial console
(e.g., using /dev/ttyUSB0) instead of SSH.
"""

from wrtkit import UCIConfig, SerialConnection


def main():
    print("=" * 70)
    print("WRTKit Serial Console Example")
    print("=" * 70)

    # Create configuration
    config = UCIConfig()

    # Configure network interface
    config.network.interface("lan") \
        .device("eth0") \
        .proto("static") \
        .ipaddr("192.168.1.1") \
        .netmask("255.255.255.0")

    # Configure wireless
    config.wireless.radio("radio0") \
        .channel(11) \
        .htmode("HT20")

    config.wireless.wifi_iface("default_radio0") \
        .device("radio0") \
        .network("lan") \
        .mode("ap") \
        .ssid("MyOpenWRT") \
        .encryption("psk2") \
        .key("mypassword123")

    print("\n" + "=" * 70)
    print("Configuration Summary")
    print("=" * 70)
    print(f"Total UCI commands: {len(config.get_all_commands())}")

    # Connect via serial console
    # IMPORTANT: Adjust these parameters for your setup
    # Common serial ports:
    #   Linux: /dev/ttyUSB0, /dev/ttyACM0
    #   macOS: /dev/tty.usbserial-*
    #   Windows: COM3, COM4, etc.

    print("\n" + "=" * 70)
    print("Connecting to Serial Console")
    print("=" * 70)

    try:
        # Create serial connection
        # Note: You may need to adjust the port and baudrate
        serial = SerialConnection(
            port="/dev/ttyUSB0",      # Change to your serial port
            baudrate=115200,           # Most OpenWRT devices use 115200
            timeout=5.0,               # Command timeout in seconds
            prompt=r"root@[^:]+:.*[#\$]",  # Shell prompt pattern
            # If your device requires login:
            # login_username="root",
            # login_password="yourpassword",
        )

        print(f"Connecting to {serial.port}...")

        # You can use the serial connection just like SSH!
        with serial:
            print("✓ Connected successfully")

            # Get diff between local config and remote device
            print("\n" + "=" * 70)
            print("Configuration Diff")
            print("=" * 70)

            diff = config.diff(serial)

            if diff.is_empty():
                print("No differences found - configuration matches remote device")
            else:
                # Show diff in tree format
                print(diff.to_tree())

                # Ask user if they want to apply
                print("\n" + "=" * 70)
                print("Apply Configuration?")
                print("=" * 70)

                response = input("Apply these changes to the device? (yes/no): ")

                if response.lower() == "yes":
                    print("\nApplying configuration...")
                    config.apply(serial)
                    print("✓ Configuration applied successfully!")
                else:
                    print("Configuration not applied.")

    except ConnectionError as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check that the serial port exists (ls /dev/tty*)")
        print("2. Ensure you have permission to access the port")
        print("   (add your user to 'dialout' group: sudo usermod -a -G dialout $USER)")
        print("3. Verify the baudrate matches your device (usually 115200)")
        print("4. Make sure no other program is using the serial port (like picocom)")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_connection():
    """Test serial connection without applying config."""
    print("Testing serial connection...")

    try:
        serial = SerialConnection(port="/dev/ttyUSB0", baudrate=115200)

        with serial:
            print("✓ Connection established")

            # Test basic command
            stdout, stderr, exit_code = serial.execute("uname -a")
            print(f"\nDevice info: {stdout}")

            # Test UCI command
            stdout, stderr, exit_code = serial.execute("uci export network")
            print(f"\nNetwork config preview (first 200 chars):\n{stdout[:200]}...")

    except Exception as e:
        print(f"❌ Connection test failed: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run connection test only
        test_connection()
    else:
        # Run full example
        main()
