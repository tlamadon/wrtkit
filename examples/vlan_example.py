#!/usr/bin/env python3
"""
VLAN Configuration Examples for OpenWRT using wrtkit.

This example demonstrates various VLAN configurations:
1. 802.1Q VLAN tagging on a single interface
2. Bridge VLAN filtering for managed switches
3. VLAN trunk ports with multiple VLANs
4. Mixed tagged and untagged VLAN traffic
5. Inter-VLAN routing setup
"""

from wrtkit.network import NetworkConfig, NetworkDevice, NetworkInterface, BridgeVLAN


def example_basic_8021q_vlan() -> None:
    """
    Example 1: Basic 802.1Q VLAN on a single interface.

    This creates VLAN 10 and VLAN 20 on eth0 interface.
    Useful for connecting to a managed switch with VLANs.
    """
    print("\n=== Example 1: Basic 802.1Q VLANs ===")

    net = NetworkConfig()

    # Create VLAN 10 device (tagged)
    vlan10_dev = (
        NetworkDevice("vlan10")
        .with_type("8021q")
        .with_ifname("eth0")
        .with_vid(10)
        .with_name("eth0.10")
    )

    # Create VLAN 20 device (tagged)
    vlan20_dev = (
        NetworkDevice("vlan20")
        .with_type("8021q")
        .with_ifname("eth0")
        .with_vid(20)
        .with_name("eth0.20")
    )

    # Create interface for VLAN 10 with static IP
    vlan10_iface = (
        NetworkInterface("guest")
        .with_device("eth0.10")
        .with_static_ip("192.168.10.1", "255.255.255.0")
    )

    # Create interface for VLAN 20 with static IP
    vlan20_iface = (
        NetworkInterface("iot")
        .with_device("eth0.20")
        .with_static_ip("192.168.20.1", "255.255.255.0")
    )

    net.add_device(vlan10_dev)
    net.add_device(vlan20_dev)
    net.add_interface(vlan10_iface)
    net.add_interface(vlan20_iface)

    # Print UCI commands
    for cmd in net.get_commands():
        print(f"  {cmd}")

    print("\nThis configuration creates:")
    print("  - VLAN 10 on eth0 with IP 192.168.10.1/24 (guest network)")
    print("  - VLAN 20 on eth0 with IP 192.168.20.1/24 (IoT network)")


def example_bridge_vlan_filtering() -> None:
    """
    Example 2: Bridge VLAN filtering for managed switch scenarios.

    This creates a VLAN-aware bridge with different VLANs on different ports.
    Port tagging format:
    - port:t  = tagged (trunk port)
    - port:u* = untagged and PVID (access port)
    - port:*  = tagged only, no PVID change
    """
    print("\n=== Example 2: Bridge VLAN Filtering ===")

    net = NetworkConfig()

    # Create a VLAN-aware bridge
    bridge = (
        NetworkDevice("br_trunk")
        .with_name("br-trunk")
        .with_type("bridge")
        .with_ports(["lan1", "lan2", "lan3", "lan4"])
    )

    # VLAN 10: Guest network on lan1 and lan2 (untagged/access)
    vlan10 = (
        BridgeVLAN("vlan10")
        .with_device("br-trunk")
        .with_vlan(10)
        .with_port("lan1:u*")  # Untagged access port
        .with_port("lan2:u*")  # Untagged access port
        .with_port("lan4:t")   # Tagged trunk port
    )

    # VLAN 20: IoT network on lan3 (untagged/access)
    vlan20 = (
        BridgeVLAN("vlan20")
        .with_device("br-trunk")
        .with_vlan(20)
        .with_port("lan3:u*")  # Untagged access port
        .with_port("lan4:t")   # Tagged trunk port
    )

    # Create bridge interface with VLAN 10
    br_vlan10_dev = (
        NetworkDevice("br_vlan10")
        .with_type("8021q")
        .with_ifname("br-trunk")
        .with_vid(10)
        .with_name("br-trunk.10")
    )

    # Create bridge interface with VLAN 20
    br_vlan20_dev = (
        NetworkDevice("br_vlan20")
        .with_type("8021q")
        .with_ifname("br-trunk")
        .with_vid(20)
        .with_name("br-trunk.20")
    )

    # Interface for VLAN 10
    guest_iface = (
        NetworkInterface("guest")
        .with_device("br-trunk.10")
        .with_static_ip("192.168.10.1", "255.255.255.0")
    )

    # Interface for VLAN 20
    iot_iface = (
        NetworkInterface("iot")
        .with_device("br-trunk.20")
        .with_static_ip("192.168.20.1", "255.255.255.0")
    )

    net.add_device(bridge)
    net.add_bridge_vlan(vlan10)
    net.add_bridge_vlan(vlan20)
    net.add_device(br_vlan10_dev)
    net.add_device(br_vlan20_dev)
    net.add_interface(guest_iface)
    net.add_interface(iot_iface)

    # Print UCI commands
    for cmd in net.get_commands():
        print(f"  {cmd}")

    print("\nThis configuration creates:")
    print("  - Bridge br-trunk with VLAN filtering enabled")
    print("  - VLAN 10: lan1, lan2 (untagged), lan4 (tagged)")
    print("  - VLAN 20: lan3 (untagged), lan4 (tagged)")
    print("  - lan4 is a trunk port carrying both VLANs")


def example_vlan_trunk_with_multiple_vlans() -> None:
    """
    Example 3: Multiple VLANs on a trunk port.

    This creates a trunk port connecting to a managed switch,
    carrying multiple VLANs (10, 20, 30).
    """
    print("\n=== Example 3: Multiple VLANs on Trunk Port ===")

    net = NetworkConfig()

    # Create VLAN devices for VLANs 10, 20, 30 on eth1 trunk
    vlans = [10, 20, 30]
    networks = {
        10: ("guest", "192.168.10.1"),
        20: ("iot", "192.168.20.1"),
        30: ("cameras", "192.168.30.1"),
    }

    for vlan_id in vlans:
        # Create VLAN device
        vlan_dev = (
            NetworkDevice(f"vlan{vlan_id}")
            .with_type("8021q")
            .with_ifname("eth1")
            .with_vid(vlan_id)
            .with_name(f"eth1.{vlan_id}")
        )
        net.add_device(vlan_dev)

        # Create interface for this VLAN
        iface_name, ip_addr = networks[vlan_id]
        vlan_iface = (
            NetworkInterface(iface_name)
            .with_device(f"eth1.{vlan_id}")
            .with_static_ip(ip_addr, "255.255.255.0")
        )
        net.add_interface(vlan_iface)

    # Print UCI commands
    for cmd in net.get_commands():
        print(f"  {cmd}")

    print("\nThis configuration creates:")
    print("  - eth1 as trunk port carrying VLANs 10, 20, 30")
    print("  - VLAN 10: 192.168.10.1/24 (guest)")
    print("  - VLAN 20: 192.168.20.1/24 (iot)")
    print("  - VLAN 30: 192.168.30.1/24 (cameras)")


def example_vlan_on_batman_adv() -> None:
    """
    Example 4: VLANs on top of batman-adv mesh interface.

    This demonstrates how to create VLANs on a batman-adv
    mesh interface for network segmentation in a mesh network.
    """
    print("\n=== Example 4: VLANs on batman-adv ===")

    net = NetworkConfig()

    # Create batman-adv interface
    bat0_iface = (
        NetworkInterface("bat0")
        .with_proto("batadv")
        .with_routing_algo("BATMAN_V")
        .with_mtu(1500)
    )

    # Create VLAN 10 on bat0
    bat0_vlan10 = (
        NetworkDevice("bat0_vlan10")
        .with_type("8021q")
        .with_ifname("bat0")
        .with_vid(10)
        .with_name("bat0.10")
    )

    # Create VLAN 20 on bat0
    bat0_vlan20 = (
        NetworkDevice("bat0_vlan20")
        .with_type("8021q")
        .with_ifname("bat0")
        .with_vid(20)
        .with_name("bat0.20")
    )

    # Create bridge for VLAN 10 (for local clients)
    br_mesh_guest = (
        NetworkDevice("br_mesh_guest")
        .with_type("bridge")
        .with_name("br-mesh-guest")
        .with_ports(["bat0.10", "wlan0-guest"])
    )

    # Create bridge for VLAN 20 (for local clients)
    br_mesh_iot = (
        NetworkDevice("br_mesh_iot")
        .with_type("bridge")
        .with_name("br-mesh-iot")
        .with_ports(["bat0.20", "wlan0-iot"])
    )

    # Interface for guest network on mesh
    mesh_guest_iface = (
        NetworkInterface("mesh_guest")
        .with_device("br-mesh-guest")
        .with_static_ip("192.168.10.1", "255.255.255.0")
    )

    # Interface for IoT network on mesh
    mesh_iot_iface = (
        NetworkInterface("mesh_iot")
        .with_device("br-mesh-iot")
        .with_static_ip("192.168.20.1", "255.255.255.0")
    )

    net.add_interface(bat0_iface)
    net.add_device(bat0_vlan10)
    net.add_device(bat0_vlan20)
    net.add_device(br_mesh_guest)
    net.add_device(br_mesh_iot)
    net.add_interface(mesh_guest_iface)
    net.add_interface(mesh_iot_iface)

    # Print UCI commands
    for cmd in net.get_commands():
        print(f"  {cmd}")

    print("\nThis configuration creates:")
    print("  - batman-adv mesh interface (bat0)")
    print("  - VLAN 10 on bat0 bridged with wlan0-guest")
    print("  - VLAN 20 on bat0 bridged with wlan0-iot")
    print("  - Mesh network segmentation for different services")


def example_port_based_vlan_isolation() -> None:
    """
    Example 5: Port-based VLAN isolation.

    This creates isolated VLANs on different physical ports
    for complete network segmentation.
    """
    print("\n=== Example 5: Port-based VLAN Isolation ===")

    net = NetworkConfig()

    # Create a VLAN-aware bridge
    bridge = (
        NetworkDevice("br_isolated")
        .with_name("br-isolated")
        .with_type("bridge")
        .with_ports(["lan1", "lan2", "lan3", "lan4"])
    )

    # Each port gets its own VLAN (complete isolation)
    port_vlans = [
        ("lan1", 101, "office"),
        ("lan2", 102, "lab"),
        ("lan3", 103, "guest"),
        ("lan4", 104, "servers"),
    ]

    for port, vlan_id, network_name in port_vlans:
        # Create bridge VLAN for this port
        bridge_vlan = (
            BridgeVLAN(f"vlan{vlan_id}")
            .with_device("br-isolated")
            .with_vlan(vlan_id)
            .with_port(f"{port}:u*")  # Untagged access port
        )
        net.add_bridge_vlan(bridge_vlan)

        # Create 802.1Q device for the VLAN
        vlan_dev = (
            NetworkDevice(f"br_vlan{vlan_id}")
            .with_type("8021q")
            .with_ifname("br-isolated")
            .with_vid(vlan_id)
            .with_name(f"br-isolated.{vlan_id}")
        )
        net.add_device(vlan_dev)

        # Create interface for this VLAN
        vlan_iface = (
            NetworkInterface(network_name)
            .with_device(f"br-isolated.{vlan_id}")
            .with_static_ip(f"192.168.{vlan_id}.1", "255.255.255.0")
        )
        net.add_interface(vlan_iface)

    net.add_device(bridge)

    # Print UCI commands
    for cmd in net.get_commands():
        print(f"  {cmd}")

    print("\nThis configuration creates:")
    print("  - Isolated VLANs on each port:")
    print("    * lan1: VLAN 101 (192.168.101.0/24) - office")
    print("    * lan2: VLAN 102 (192.168.102.0/24) - lab")
    print("    * lan3: VLAN 103 (192.168.103.0/24) - guest")
    print("    * lan4: VLAN 104 (192.168.104.0/24) - servers")


def example_inter_vlan_routing() -> None:
    """
    Example 6: Inter-VLAN routing setup.

    This creates multiple VLANs that can route between each other
    through the OpenWRT router (router-on-a-stick).
    """
    print("\n=== Example 6: Inter-VLAN Routing (Router-on-a-stick) ===")

    net = NetworkConfig()

    # Create VLAN devices on eth0 (connected to managed switch)
    vlans = [
        (10, "192.168.10.1", "management"),
        (20, "192.168.20.1", "office"),
        (30, "192.168.30.1", "guest"),
        (40, "192.168.40.1", "servers"),
    ]

    for vlan_id, ip_addr, network_name in vlans:
        # Create VLAN device
        vlan_dev = (
            NetworkDevice(f"vlan{vlan_id}")
            .with_type("8021q")
            .with_ifname("eth0")
            .with_vid(vlan_id)
            .with_name(f"eth0.{vlan_id}")
        )
        net.add_device(vlan_dev)

        # Create interface for routing
        vlan_iface = (
            NetworkInterface(network_name)
            .with_device(f"eth0.{vlan_id}")
            .with_static_ip(ip_addr, "255.255.255.0")
        )
        net.add_interface(vlan_iface)

    # Print UCI commands
    for cmd in net.get_commands():
        print(f"  {cmd}")

    print("\nThis configuration creates:")
    print("  - Router-on-a-stick configuration")
    print("  - eth0 carries all VLANs (trunk)")
    print("  - OpenWRT routes between VLANs:")
    print("    * VLAN 10: 192.168.10.0/24 (management)")
    print("    * VLAN 20: 192.168.20.0/24 (office)")
    print("    * VLAN 30: 192.168.30.0/24 (guest)")
    print("    * VLAN 40: 192.168.40.0/24 (servers)")
    print("\n  Note: Add firewall rules to control inter-VLAN traffic!")


def main() -> None:
    """Run all VLAN examples."""
    print("=" * 70)
    print("OpenWRT VLAN Configuration Examples using wrtkit")
    print("=" * 70)

    example_basic_8021q_vlan()
    example_bridge_vlan_filtering()
    example_vlan_trunk_with_multiple_vlans()
    example_vlan_on_batman_adv()
    example_port_based_vlan_isolation()
    example_inter_vlan_routing()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nPort tagging reference:")
    print("  port:t   = Tagged (trunk port)")
    print("  port:u*  = Untagged and PVID (access port)")
    print("  port:*   = Tagged only, no PVID")
    print("  port:u   = Untagged only")
    print("\nFor more information, see:")
    print("  - OpenWRT VLAN docs: https://openwrt.org/docs/guide-user/network/vlan/")
    print("  - Bridge VLAN: https://openwrt.org/docs/guide-user/network/vlan/switch_configuration")


if __name__ == "__main__":
    main()
