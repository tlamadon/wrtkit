#!/usr/bin/env python3
"""
Example configuration that mirrors the router.cfg file.
This demonstrates how to use wrtkit to define OpenWRT configuration in Python.
"""

from wrtkit import UCIConfig


def create_router_config() -> UCIConfig:
    """Create the router configuration."""
    config = UCIConfig()

    # =====================
    # LAN BRIDGE
    # =====================
    config.network.device("br_lan").name("br-lan").type("bridge").add_port("lan1").add_port(
        "lan2"
    ).add_port("lan3")

    config.network.interface("lan").device("br-lan").proto("static").ipaddr("192.168.10.1").netmask(
        "255.255.255.0"
    )

    # =====================
    # WAN
    # =====================
    config.network.interface("wan").device("eth1").proto("dhcp")

    # =====================
    # DHCP
    # =====================
    config.dhcp.dhcp("lan").interface("lan").start(100).limit(150).leasetime("12h").ignore(False)

    # =====================
    # FIREWALL
    # =====================
    config.firewall.zone(0).name("lan").input("ACCEPT").output("ACCEPT").forward(
        "ACCEPT"
    ).add_network("lan")

    config.firewall.zone(1).name("wan").input("REJECT").output("ACCEPT").forward("REJECT").masq(
        True
    ).mtu_fix(True).add_network("wan")

    config.firewall.forwarding(0).src("lan").dest("wan")

    # =====================
    # BATMAN-ADV
    # =====================
    config.network.interface("bat0").proto("batadv").routing_algo("BATMAN_IV").gw_mode(
        "server"
    ).gw_bandwidth("10000/10000").hop_penalty(30).orig_interval(1000)

    config.network.device("bat0_vlan10").type("8021q").ifname("bat0").vid(10).name("bat0.10")

    # Add bat0.10 to the bridge (note: this would need to be added to the existing br_lan)
    # In practice, you might need to handle this differently depending on your use case

    config.network.interface("mesh0").proto("batadv_hardif").master("bat0")

    # =====================
    # WIRELESS
    # =====================
    config.wireless.radio("radio0").channel(11).htmode("HT20").country("US").disabled(False)

    config.wireless.radio("radio1").channel(149).country("US").disabled(False)

    config.wireless.wifi_iface("ap_two").device("radio0").mode("ap").network("lan").ssid(
        "MyNetwork-2G"
    ).encryption("psk2").key("YourSecurePassword123").ieee80211r(True).ft_over_ds(
        True
    ).ft_psk_generate_local(True)

    config.wireless.wifi_iface("ap_five").device("radio1").mode("ap").network("lan").ssid(
        "MyNetwork-5G"
    ).encryption("psk2").key("YourSecurePassword123").ieee80211r(True).ft_over_ds(
        True
    ).ft_psk_generate_local(True)

    config.wireless.wifi_iface("mesh0_iface").device("radio1").mode("mesh").ifname("mesh0").network(
        "mesh0"
    ).mesh_id("MyMeshNetwork").encryption("sae").key("MeshPassword123").mesh_fwding(
        False
    ).mcast_rate(18000)

    return config


def main():
    """Main function demonstrating different use cases."""
    # Create the configuration
    config = create_router_config()

    # Option 1: Save to a script file
    print("Saving configuration to script file...")
    config.save_to_file("generated_router_config.sh")
    print("Configuration saved to generated_router_config.sh")

    # Option 2: Print the configuration
    print("\n" + "=" * 60)
    print("Generated UCI Configuration:")
    print("=" * 60)
    print(config.to_script())

    # Option 3: Apply to a remote device (commented out - uncomment and configure to use)
    # ssh = SSHConnection(
    #     host="192.168.1.1",
    #     username="root",
    #     password="your-password",  # or use key_filename="/path/to/key"
    # )
    #
    # # Show the diff first
    # print("\n" + "=" * 60)
    # print("Configuration Diff:")
    # print("=" * 60)
    # diff = config.diff(ssh)
    # print(diff)
    #
    # # Apply if you want to
    # if input("\nApply configuration? (y/n): ").lower() == "y":
    #     config.apply(ssh, dry_run=False, auto_commit=True, auto_reload=True)
    #     print("Configuration applied successfully!")


if __name__ == "__main__":
    main()
