#!/usr/bin/env python3
"""
Simple example demonstrating basic wrtkit usage.
"""

from wrtkit import UCIConfig, SSHConnection


def main():
    # Create a new configuration
    config = UCIConfig()

    # Configure a simple LAN
    config.network.interface("lan") \
        .device("eth0") \
        .proto("static") \
        .ipaddr("192.168.1.1") \
        .netmask("255.255.255.0")

    # Configure WAN with DHCP
    config.network.interface("wan") \
        .device("eth1") \
        .proto("dhcp")

    # Set up DHCP server for LAN
    config.dhcp.dhcp("lan") \
        .interface("lan") \
        .start(100) \
        .limit(150) \
        .leasetime("12h")

    # Configure a simple wireless AP
    config.wireless.radio("radio0") \
        .channel(11) \
        .htmode("HT20") \
        .country("US") \
        .disabled(False)

    config.wireless.wifi_iface("default_ap") \
        .device("radio0") \
        .mode("ap") \
        .network("lan") \
        .ssid("MyNetwork") \
        .encryption("psk2") \
        .key("MySecurePassword123")

    # Basic firewall setup
    config.firewall.zone(0) \
        .name("lan") \
        .input("ACCEPT") \
        .output("ACCEPT") \
        .forward("ACCEPT") \
        .add_network("lan")

    config.firewall.zone(1) \
        .name("wan") \
        .input("REJECT") \
        .output("ACCEPT") \
        .forward("REJECT") \
        .masq(True) \
        .add_network("wan")

    config.firewall.forwarding(0) \
        .src("lan") \
        .dest("wan")

    # Print the generated configuration
    print("Generated UCI Configuration:")
    print("=" * 60)
    print(config.to_script())

    # Save to file
    config.save_to_file("simple_config.sh")
    print("\nConfiguration saved to simple_config.sh")

    # Example of using SSH (commented out)
    # ssh = SSHConnection(
    #     host="192.168.1.1",
    #     username="root",
    #     key_filename="/path/to/ssh/key"
    # )
    #
    # with ssh:
    #     # Check differences
    #     diff = config.diff(ssh)
    #     print("\nDifferences from remote:")
    #     print(diff)
    #
    #     # Apply if desired
    #     if not diff.is_empty():
    #         config.apply(ssh, dry_run=False)


if __name__ == "__main__":
    main()
