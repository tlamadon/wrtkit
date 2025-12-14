"""
Example demonstrating YAML/JSON workflow for router configuration.

This example shows how to:
1. Load a base configuration from YAML
2. Extend it programmatically
3. Save the result
4. Deploy to a router
"""

from wrtkit import UCIConfig, SSHConnection
from wrtkit.network import NetworkInterface, NetworkDevice
from wrtkit.wireless import WirelessRadio, WirelessInterface
from wrtkit.dhcp import DHCPSection
from wrtkit.firewall import FirewallZone, FirewallForwarding


def create_base_config():
    """Create a base configuration and save it to YAML."""
    print("Creating base configuration...")

    config = UCIConfig()

    # Network: Bridge for LAN ports
    bridge = NetworkDevice("br_lan") \
        .with_name("br-lan") \
        .with_type("bridge") \
        .with_ports(["lan1", "lan2", "lan3", "lan4"])
    config.network.add_device(bridge)

    # Network: LAN interface
    lan = NetworkInterface("lan") \
        .with_device("br-lan") \
        .with_static_ip("192.168.1.1", "255.255.255.0")
    config.network.add_interface(lan)

    # Network: WAN interface (DHCP)
    wan = NetworkInterface("wan") \
        .with_device("eth0") \
        .with_dhcp()
    config.network.add_interface(wan)

    # Wireless: Configure radios
    radio0 = WirelessRadio("radio0") \
        .with_channel(36) \
        .with_htmode("HE80") \
        .with_country("US") \
        .with_disabled(False)
    config.wireless.add_radio(radio0)

    radio1 = WirelessRadio("radio1") \
        .with_channel(6) \
        .with_htmode("HE20") \
        .with_country("US") \
        .with_disabled(False)
    config.wireless.add_radio(radio1)

    # DHCP: LAN DHCP server
    dhcp_lan = DHCPSection("lan") \
        .with_interface("lan") \
        .with_range(100, 200, "12h")
    config.dhcp.add_dhcp(dhcp_lan)

    # Firewall: Basic zones
    lan_zone = FirewallZone(0) \
        .with_name("lan") \
        .with_input("ACCEPT") \
        .with_output("ACCEPT") \
        .with_forward("ACCEPT") \
        .with_network("lan")
    config.firewall.add_zone(lan_zone)

    wan_zone = FirewallZone(1) \
        .with_name("wan") \
        .with_input("REJECT") \
        .with_output("ACCEPT") \
        .with_forward("REJECT") \
        .with_masq(True) \
        .with_mtu_fix(True) \
        .with_network("wan")
    config.firewall.add_zone(wan_zone)

    # Firewall: LAN to WAN forwarding
    forwarding = FirewallForwarding(0) \
        .with_src("lan") \
        .with_dest("wan")
    config.firewall.add_forwarding(forwarding)

    # Save to YAML
    config.to_yaml_file("base-router-config.yaml")
    print("✓ Saved base configuration to base-router-config.yaml")

    return config


def extend_with_guest_network():
    """Load base config and add guest network."""
    print("\nExtending with guest network...")

    # Load base configuration
    config = UCIConfig.from_yaml_file("base-router-config.yaml")
    print("✓ Loaded base configuration")

    # Add guest VLAN (VLAN 100)
    guest_vlan = NetworkDevice("guest_vlan") \
        .with_type("8021q") \
        .with_ifname("lan1") \
        .with_vid(100)
    config.network.add_device(guest_vlan)

    # Guest interface
    guest_interface = NetworkInterface("guest") \
        .with_device("lan1.100") \
        .with_static_ip("192.168.100.1", "255.255.255.0")
    config.network.add_interface(guest_interface)

    # Guest DHCP
    guest_dhcp = DHCPSection("guest") \
        .with_interface("guest") \
        .with_range(50, 100, "2h")
    config.dhcp.add_dhcp(guest_dhcp)

    # Guest WiFi on 2.4GHz
    guest_wifi = WirelessInterface("guest_radio1") \
        .with_device("radio1") \
        .with_mode("ap") \
        .with_network("guest") \
        .with_ssid("GuestNetwork") \
        .with_encryption("psk2") \
        .with_key("GuestPassword123!")
    config.wireless.add_interface(guest_wifi)

    # Guest firewall zone (isolated)
    guest_zone = FirewallZone(2) \
        .with_name("guest") \
        .with_input("REJECT") \
        .with_output("ACCEPT") \
        .with_forward("REJECT") \
        .with_network("guest")
    config.firewall.add_zone(guest_zone)

    # Allow guest to wan
    guest_forwarding = FirewallForwarding(1) \
        .with_src("guest") \
        .with_dest("wan")
    config.firewall.add_forwarding(guest_forwarding)

    # Save extended config
    config.to_yaml_file("router-config-with-guest.yaml")
    print("✓ Saved extended configuration to router-config-with-guest.yaml")

    return config


def add_multiple_aps():
    """Add multiple access points from a config list."""
    print("\nAdding multiple access points...")

    config = UCIConfig.from_yaml_file("router-config-with-guest.yaml")

    # AP configurations
    aps = [
        {
            "name": "main_5g",
            "radio": "radio0",
            "ssid": "MyNetwork-5G",
            "network": "lan",
            "encryption": "sae",
            "key": "SecurePassword123!"
        },
        {
            "name": "main_2g",
            "radio": "radio1",
            "ssid": "MyNetwork-2.4G",
            "network": "lan",
            "encryption": "sae",
            "key": "SecurePassword123!"
        },
    ]

    for ap_config in aps:
        ap = WirelessInterface(ap_config["name"]) \
            .with_device(ap_config["radio"]) \
            .with_mode("ap") \
            .with_network(ap_config["network"]) \
            .with_ssid(ap_config["ssid"]) \
            .with_encryption(ap_config["encryption"]) \
            .with_key(ap_config["key"])
        config.wireless.add_interface(ap)

    config.to_yaml_file("complete-router-config.yaml")
    print("✓ Saved complete configuration to complete-router-config.yaml")

    return config


def deploy_to_router(config_file, router_ip, dry_run=True):
    """Deploy configuration to a router."""
    print(f"\nDeploying {config_file} to router at {router_ip}...")

    # Load configuration
    config = UCIConfig.from_yaml_file(config_file)

    try:
        # Connect to router (replace with your credentials)
        with SSHConnection(
            router_ip,
            username="root",
            password="your-password"  # Or use key_filename
        ) as ssh:
            print("✓ Connected to router")

            # Compare with current configuration
            diff = config.diff(ssh)

            if diff.is_empty():
                print("✓ Configuration is already up to date")
                return

            # Show differences
            print("\nConfiguration differences:")
            print(diff.to_tree(color=True))

            if dry_run:
                print("\n[DRY RUN] Would apply these changes")
                return

            # Prompt for confirmation
            response = input("\nApply these changes? (yes/no): ")
            if response.lower() == "yes":
                config.apply(ssh)
                print("✓ Configuration applied successfully")
            else:
                print("Deployment cancelled")

    except Exception as e:
        print(f"✗ Error: {e}")


def generate_multi_site_configs():
    """Generate configurations for multiple sites."""
    print("\nGenerating multi-site configurations...")

    sites = [
        {"name": "office-main", "subnet": "192.168.1", "router_ip": "10.0.0.1"},
        {"name": "office-branch1", "subnet": "192.168.2", "router_ip": "10.0.0.2"},
        {"name": "office-branch2", "subnet": "192.168.3", "router_ip": "10.0.0.3"},
    ]

    for site in sites:
        # Load base template
        config = UCIConfig.from_yaml_file("base-router-config.yaml")

        # Update LAN IP for this site
        for interface in config.network.interfaces:
            if interface._section == "lan":
                # Update in place (or create new)
                updated = NetworkInterface("lan") \
                    .with_device("br-lan") \
                    .with_static_ip(f"{site['subnet']}.1", "255.255.255.0")

                # Replace in list
                config.network.interfaces = [
                    updated if i._section == "lan" else i
                    for i in config.network.interfaces
                ]
                break

        # Save site-specific config
        filename = f"config-{site['name']}.yaml"
        config.to_yaml_file(filename)
        print(f"✓ Generated {filename}")

    print("✓ All site configurations generated")


def main():
    """Run the example workflow."""
    print("=" * 60)
    print("YAML/JSON Workflow Example")
    print("=" * 60)

    # Step 1: Create base configuration
    create_base_config()

    # Step 2: Extend with guest network
    extend_with_guest_network()

    # Step 3: Add access points
    add_multiple_aps()

    # Step 4: Generate multi-site configs
    generate_multi_site_configs()

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - base-router-config.yaml")
    print("  - router-config-with-guest.yaml")
    print("  - complete-router-config.yaml")
    print("  - config-office-main.yaml")
    print("  - config-office-branch1.yaml")
    print("  - config-office-branch2.yaml")
    print("\nTo deploy to a router:")
    print("  deploy_to_router('complete-router-config.yaml', '192.168.1.1', dry_run=False)")


if __name__ == "__main__":
    main()
