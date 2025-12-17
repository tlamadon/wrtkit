#!/usr/bin/env python3
"""Example: Collect and display mesh network information.

This example demonstrates how to:
1. Connect to a mesh network (main router + nodes)
2. Collect information about connected clients
3. Display the results as a tree showing which AP each client is connected to
"""

from wrtkit import collect_mesh_network, display_mesh_tree


def main():
    # Collect mesh network information
    # Replace with your actual router/node IPs and credentials
    network = collect_mesh_network(
        main_host="192.168.1.1",  # Main router IP
        node_hosts=[
            "192.168.1.2",  # Mesh node 1
            "192.168.1.3",  # Mesh node 2
        ],
        username="root",
        password="your_password",  # Or use key_filename="/path/to/key"
    )

    # Display the network tree
    print(display_mesh_tree(network, use_color=True))

    # You can also access the data programmatically:
    print("\n--- Summary ---")
    total_clients = 0
    for node in network.nodes:
        wifi_clients = [c for c in node.clients if c.connection_type == "wifi"]
        lan_clients = [c for c in node.clients if c.connection_type == "lan"]
        print(f"{node.hostname or node.host}: {len(wifi_clients)} WiFi, {len(lan_clients)} LAN")
        total_clients += len(node.clients)

    print(f"Total clients: {total_clients}")


if __name__ == "__main__":
    main()
