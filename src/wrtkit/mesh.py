"""Mesh network information collection and visualization."""

import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

from .ssh import SSHConnection


class Client(BaseModel):
    """Represents a connected client/device."""

    mac: str
    ip: Optional[str] = None
    hostname: Optional[str] = None
    connection_type: Literal["lan", "wifi"]
    interface: str
    ssid: Optional[str] = None
    signal: Optional[int] = None  # dBm, only for WiFi
    via_node: Optional[str] = None  # For mesh: which AP this client is physically behind
    inactive_ms: Optional[int] = None  # Milliseconds since last activity (WiFi only)
    tx_bitrate: Optional[str] = None  # Transmit bitrate (e.g., "866.7 MBit/s")
    rx_bitrate: Optional[str] = None  # Receive bitrate
    stale: bool = False  # True if client is in ARP but not in FDB (likely disconnected)


class MeshNode(BaseModel):
    """Represents a mesh node (AP/router)."""

    host: str
    hostname: Optional[str] = None
    clients: List[Client] = []
    interfaces: Dict[str, str] = {}  # interface -> SSID mapping


class MeshNetwork(BaseModel):
    """Represents the entire mesh network."""

    nodes: List[MeshNode] = []


@dataclass
class DHCPLease:
    """Internal representation of a DHCP lease."""

    expiry: str
    mac: str
    ip: str
    hostname: str


@dataclass
class WifiStation:
    """Internal representation of a WiFi station from iw."""

    mac: str
    interface: str
    signal: Optional[int] = None
    rx_bitrate: Optional[str] = None
    tx_bitrate: Optional[str] = None
    inactive_ms: Optional[int] = None  # Milliseconds since last activity


def _parse_dhcp_leases(output: str) -> Dict[str, DHCPLease]:
    """
    Parse /tmp/dhcp.leases file output.

    Format: <expiry> <mac> <ip> <hostname> <client-id>
    Returns: Dict mapping MAC address (lowercase) to DHCPLease
    """
    leases: Dict[str, DHCPLease] = {}
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            mac = parts[1].lower()
            leases[mac] = DHCPLease(
                expiry=parts[0],
                mac=mac,
                ip=parts[2],
                hostname=parts[3] if parts[3] != "*" else "",
            )
    return leases


def _parse_wifi_stations(output: str, interface: str) -> List[WifiStation]:
    """
    Parse 'iw dev <interface> station dump' output.

    Example output:
        Station aa:bb:cc:dd:ee:ff (on wlan0)
            inactive time:  1234 ms
            rx bitrate:     866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
            tx bitrate:     866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
            signal:         -65 dBm
            ...

    Returns: List of WifiStation objects
    """
    stations: List[WifiStation] = []
    current_mac: Optional[str] = None
    current_signal: Optional[int] = None
    current_inactive_ms: Optional[int] = None
    current_tx_bitrate: Optional[str] = None
    current_rx_bitrate: Optional[str] = None

    for line in output.split("\n"):
        line = line.strip()

        # New station entry: "Station aa:bb:cc:dd:ee:ff (on wlan0)"
        station_match = re.match(r"Station ([0-9a-fA-F:]+)", line)
        if station_match:
            if current_mac:
                stations.append(
                    WifiStation(
                        mac=current_mac.lower(),
                        interface=interface,
                        signal=current_signal,
                        inactive_ms=current_inactive_ms,
                        tx_bitrate=current_tx_bitrate,
                        rx_bitrate=current_rx_bitrate,
                    )
                )
            current_mac = station_match.group(1)
            current_signal = None
            current_inactive_ms = None
            current_tx_bitrate = None
            current_rx_bitrate = None
            continue

        if not current_mac:
            continue

        # Signal strength: "signal: -65 dBm" or "signal avg: -65 dBm"
        signal_match = re.match(r"signal:\s*(-?\d+)\s*dBm", line)
        if signal_match:
            current_signal = int(signal_match.group(1))
            continue

        # Inactive time: "inactive time: 1234 ms"
        inactive_match = re.match(r"inactive time:\s*(\d+)\s*ms", line)
        if inactive_match:
            current_inactive_ms = int(inactive_match.group(1))
            continue

        # TX bitrate: "tx bitrate: 866.7 MBit/s VHT-MCS 9 ..."
        tx_match = re.match(r"tx bitrate:\s*(.+)", line)
        if tx_match:
            # Extract just the speed part (e.g., "866.7 MBit/s")
            bitrate = tx_match.group(1)
            speed_match = re.match(r"([\d.]+\s*[MKG]?Bit/s)", bitrate)
            current_tx_bitrate = speed_match.group(1) if speed_match else bitrate.split()[0]
            continue

        # RX bitrate: "rx bitrate: 866.7 MBit/s VHT-MCS 9 ..."
        rx_match = re.match(r"rx bitrate:\s*(.+)", line)
        if rx_match:
            bitrate = rx_match.group(1)
            speed_match = re.match(r"([\d.]+\s*[MKG]?Bit/s)", bitrate)
            current_rx_bitrate = speed_match.group(1) if speed_match else bitrate.split()[0]
            continue

    # Don't forget the last station
    if current_mac:
        stations.append(
            WifiStation(
                mac=current_mac.lower(),
                interface=interface,
                signal=current_signal,
                inactive_ms=current_inactive_ms,
                tx_bitrate=current_tx_bitrate,
                rx_bitrate=current_rx_bitrate,
            )
        )

    return stations


def _parse_arp_table(output: str) -> Dict[str, str]:
    """
    Parse /proc/net/arp output.

    Returns: Dict mapping MAC address (lowercase) to IP address
    """
    mac_to_ip: Dict[str, str] = {}

    for line in output.strip().split("\n"):
        # Skip header line
        if line.startswith("IP address"):
            continue

        parts = line.split()
        if len(parts) >= 4:
            ip = parts[0]
            mac = parts[3].lower()
            # Skip incomplete entries (00:00:00:00:00:00)
            if mac != "00:00:00:00:00:00":
                mac_to_ip[mac] = ip

    return mac_to_ip


def _parse_bridge_fdb(output: str) -> Dict[str, str]:
    """
    Parse 'bridge fdb show' output.

    Format: "aa:bb:cc:dd:ee:ff dev eth0 master br-lan"
    Returns: Dict mapping MAC address (lowercase) to device name
    """
    mac_to_device: Dict[str, str] = {}

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        # Parse: "aa:bb:cc:dd:ee:ff dev eth0 master br-lan [self] [offload]"
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "dev":
            mac = parts[0].lower()
            device = parts[2]
            # Skip entries that are "self" (local to bridge) or "permanent"
            if "self" not in line and "permanent" not in line:
                mac_to_device[mac] = device

    return mac_to_device


def _get_batman_translation_table(connection: SSHConnection) -> Dict[str, str]:
    """
    Get BATMAN-ADV translation table mapping client MACs to their originator (mesh node).

    Uses 'batctl tg' (transglobal table) to find which mesh node each client is behind.

    Returns: Dict mapping client MAC (lowercase) to originator MAC (the mesh node's MAC)
    """
    client_to_originator: Dict[str, str] = {}

    # Find batman interfaces
    stdout, _, _ = connection.execute("ls /sys/class/net/*/batman_adv 2>/dev/null | cut -d/ -f5")
    bat_ifaces = [iface.strip() for iface in stdout.split("\n") if iface.strip()]

    for bat_iface in bat_ifaces:
        # Try batctl with mesh interface specified (-m option for newer versions)
        # batctl tg = transglobal table (shows all clients in the mesh)
        # Typical output formats:
        # " * aa:bb:cc:dd:ee:ff   -1 [.P....]   0.000   (cc:dd:ee:ff:00:11)"
        # "   aa:bb:cc:dd:ee:ff   -1 [.P....]   0.000   (cc:dd:ee:ff:00:11)"
        for cmd in [
            f"batctl meshif {bat_iface} tg 2>/dev/null",
            f"batctl -m {bat_iface} tg 2>/dev/null",
            "batctl tg 2>/dev/null",
        ]:
            stdout, _, exit_code = connection.execute(cmd)
            if exit_code == 0 and stdout.strip():
                for line in stdout.split("\n"):
                    # Skip header and empty lines
                    if not line.strip() or "Client" in line or "---" in line:
                        continue

                    # Find all MAC addresses in the line
                    mac_pattern = r"[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}"
                    macs = re.findall(mac_pattern, line)

                    if len(macs) >= 2:
                        # First MAC is the client, second MAC is the originator
                        client_mac = macs[0].lower()
                        originator_mac = macs[1].lower()
                        client_to_originator[client_mac] = originator_mac
                    elif len(macs) == 1:
                        # Only one MAC - this might be a local client (on this node)
                        # Check if the line indicates it's local
                        if "[.P....]" in line or "local" in line.lower():
                            # Local client - don't add to mapping (will be handled by local node)
                            pass

                if client_to_originator:
                    break
        if client_to_originator:
            break

    return client_to_originator


def _get_batman_originators(connection: SSHConnection) -> Dict[str, str]:
    """
    Get BATMAN-ADV originator table mapping originator MACs to their hostnames/IPs.

    Uses 'batctl o' to get the list of mesh nodes.

    Returns: Dict mapping originator MAC (lowercase) to best next-hop interface
    """
    originators: Dict[str, str] = {}

    stdout, _, _ = connection.execute("ls /sys/class/net/*/batman_adv 2>/dev/null | cut -d/ -f5")
    bat_ifaces = [iface.strip() for iface in stdout.split("\n") if iface.strip()]

    for bat_iface in bat_ifaces:
        for cmd in [
            f"batctl meshif {bat_iface} o 2>/dev/null",
            f"batctl -m {bat_iface} o 2>/dev/null",
            "batctl o 2>/dev/null",
        ]:
            stdout, _, exit_code = connection.execute(cmd)
            if exit_code == 0 and stdout.strip():
                for line in stdout.split("\n"):
                    if not line.strip() or "Originator" in line or "---" in line:
                        continue
                    # Format: " * aa:bb:cc:dd:ee:ff ... [ next_hop_mac] ..."
                    parts = line.split()
                    for part in parts:
                        if re.match(r"^[0-9a-fA-F:]{17}$", part):
                            originators[part.lower()] = bat_iface
                            break
                if originators:
                    break
        if originators:
            break

    return originators


def _get_bridge_port_mapping(connection: SSHConnection) -> Dict[str, str]:
    """
    Get mapping of MAC addresses to the physical port/device they're connected to.

    Uses 'bridge fdb show' to determine which bridge port learned each MAC.

    Returns: Dict mapping MAC (lowercase) to device name (e.g., 'lan1', 'eth0.1')
    """
    mac_to_device: Dict[str, str] = {}

    # Method 1: Use 'bridge fdb show' (modern Linux)
    stdout, _, exit_code = connection.execute("bridge fdb show 2>/dev/null")
    if exit_code == 0 and stdout.strip():
        mac_to_device = _parse_bridge_fdb(stdout)

    # Method 2: Fallback to brctl showmacs for each bridge
    if not mac_to_device:
        # Find all bridges
        stdout, _, _ = connection.execute("ls /sys/class/net/*/bridge 2>/dev/null | cut -d/ -f5")
        bridges = [b.strip() for b in stdout.split("\n") if b.strip()]

        for bridge in bridges:
            # Get port number to interface mapping
            stdout, _, _ = connection.execute(f"ls /sys/class/net/{bridge}/brif/ 2>/dev/null")
            port_ifaces = [p.strip() for p in stdout.split("\n") if p.strip()]

            # Get port numbers
            port_to_iface: Dict[str, str] = {}
            for iface in port_ifaces:
                stdout, _, _ = connection.execute(
                    f"cat /sys/class/net/{bridge}/brif/{iface}/port_no 2>/dev/null"
                )
                port_no = stdout.strip()
                if port_no:
                    # Port number is in hex, convert to decimal string
                    try:
                        port_to_iface[str(int(port_no, 16))] = iface
                    except ValueError:
                        pass

            # Now get MACs from brctl
            stdout, _, exit_code = connection.execute(f"brctl showmacs {bridge} 2>/dev/null")
            if exit_code == 0:
                for line in stdout.split("\n"):
                    if line.startswith("port no") or not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 3:
                        port_no = parts[0]
                        mac = parts[1].lower()
                        is_local = parts[2]
                        if is_local == "no" and port_no in port_to_iface:
                            mac_to_device[mac] = port_to_iface[port_no]

    return mac_to_device


def _get_interface_ssids(connection: SSHConnection) -> Dict[str, str]:
    """
    Get mapping of wireless interfaces to their SSIDs.

    Uses multiple methods to ensure we get the SSID:
    1. UCI configuration (wireless.*.ssid with wireless.*.ifname)
    2. iwinfo (OpenWRT's wireless info tool)
    3. iw dev (standard Linux wireless tool)
    4. Individual iw <iface> info queries

    Returns: Dict mapping interface name to SSID
    """
    interface_to_ssid: Dict[str, str] = {}

    # Method 1: Get wireless configuration from UCI
    stdout, _, _ = connection.execute("uci show wireless")

    # Parse for interface names and SSIDs
    # wireless.default_radio0.ifname='wlan0'
    # wireless.default_radio0.ssid='MyNetwork'
    section_data: Dict[str, Dict[str, str]] = {}

    for line in stdout.split("\n"):
        if not line.strip():
            continue

        match = re.match(r"wireless\.([^.]+)\.(\w+)='?([^']*)'?", line)
        if match:
            section = match.group(1)
            key = match.group(2)
            value = match.group(3)

            if section not in section_data:
                section_data[section] = {}
            section_data[section][key] = value

    # Build interface -> SSID mapping from UCI
    for section, data in section_data.items():
        ifname = data.get("ifname")
        ssid = data.get("ssid")
        if ifname and ssid:
            interface_to_ssid[ifname] = ssid

    # Method 2: Try iwinfo (OpenWRT specific, most reliable)
    stdout, _, exit_code = connection.execute("iwinfo 2>/dev/null")
    if exit_code == 0:
        # iwinfo output format:
        # wlan0     ESSID: "MyNetwork"
        #           Access Point: ...
        current_iface = None
        for line in stdout.split("\n"):
            # Interface line: "wlan0     ESSID: ..."
            iface_match = re.match(r"^(\S+)\s+ESSID:\s*\"([^\"]+)\"", line)
            if iface_match:
                iface = iface_match.group(1)
                ssid = iface_match.group(2)
                if ssid and ssid != "unknown":
                    interface_to_ssid[iface] = ssid

    # Method 3: Try iw dev (standard Linux)
    stdout, _, exit_code = connection.execute("iw dev 2>/dev/null")
    if exit_code == 0:
        current_iface = None
        for line in stdout.split("\n"):
            iface_match = re.match(r"\s*Interface\s+(\S+)", line)
            if iface_match:
                current_iface = iface_match.group(1)
                continue

            ssid_match = re.match(r"\s*ssid\s+(.+)", line)
            if ssid_match and current_iface and current_iface not in interface_to_ssid:
                interface_to_ssid[current_iface] = ssid_match.group(1).strip()

    # Method 4: Query each interface directly if still missing
    # Get list of wireless interfaces
    stdout, _, _ = connection.execute("ls -1 /sys/class/net/*/wireless 2>/dev/null | cut -d/ -f5")
    wifi_ifaces = [iface.strip() for iface in stdout.split("\n") if iface.strip()]

    for iface in wifi_ifaces:
        if iface not in interface_to_ssid:
            # Try iw <iface> info
            stdout, _, exit_code = connection.execute(f"iw dev {iface} info 2>/dev/null")
            if exit_code == 0:
                for line in stdout.split("\n"):
                    ssid_match = re.match(r"\s*ssid\s+(.+)", line)
                    if ssid_match:
                        interface_to_ssid[iface] = ssid_match.group(1).strip()
                        break

            # Also try iwinfo for this specific interface
            if iface not in interface_to_ssid:
                stdout, _, exit_code = connection.execute(f"iwinfo {iface} info 2>/dev/null")
                if exit_code == 0:
                    essid_match = re.search(r'ESSID:\s*"([^"]+)"', stdout)
                    if essid_match:
                        interface_to_ssid[iface] = essid_match.group(1)

    return interface_to_ssid


def _get_wireless_interfaces(connection: SSHConnection) -> List[str]:
    """Get list of wireless interface names."""
    interfaces: List[str] = []

    # Try iw dev first
    stdout, _, exit_code = connection.execute("iw dev 2>/dev/null")
    if exit_code == 0:
        for line in stdout.split("\n"):
            match = re.match(r"\s*Interface\s+(\S+)", line)
            if match:
                interfaces.append(match.group(1))

    # Fallback to listing /sys/class/ieee80211
    if not interfaces:
        stdout, _, _ = connection.execute("ls /sys/class/net/*/wireless 2>/dev/null | cut -d/ -f5")
        interfaces = [iface.strip() for iface in stdout.split("\n") if iface.strip()]

    return interfaces


def _get_hostname(connection: SSHConnection) -> str:
    """Get the hostname of the device."""
    stdout, _, _ = connection.execute("uci get system.@system[0].hostname 2>/dev/null")
    hostname = stdout.strip()
    if not hostname:
        stdout, _, _ = connection.execute("hostname")
        hostname = stdout.strip()
    return hostname or "unknown"


@dataclass
class _NodeRawData:
    """Internal: raw data collected from a node before deduplication."""

    host: str
    hostname: str
    interface_ssids: Dict[str, str]
    wifi_clients: List[Client]
    arp_table: Dict[str, str]
    dhcp_leases: Dict[str, DHCPLease]
    bridge_fdb: Dict[str, str]  # MAC -> physical port/device
    batman_tt: Dict[str, str]  # client MAC -> originator MAC (mesh node)
    node_mac: Optional[str] = None  # This node's batman originator MAC


def _get_node_batman_mac(connection: SSHConnection) -> Optional[str]:
    """Get this node's BATMAN-ADV originator MAC address.

    The originator MAC is the primary address that identifies this node in the mesh.
    It's typically the MAC of the primary hard interface or can be found via batctl.
    """
    stdout, _, _ = connection.execute("ls /sys/class/net/*/batman_adv 2>/dev/null | cut -d/ -f5")
    bat_ifaces = [iface.strip() for iface in stdout.split("\n") if iface.strip()]

    for bat_iface in bat_ifaces:
        # Method 1: Try reading the primary/originator address directly (sysfs paths)
        for path in [
            f"/sys/class/net/{bat_iface}/mesh/orig_address",
            f"/sys/class/net/{bat_iface}/batman_adv/orig_address",
        ]:
            stdout, _, exit_code = connection.execute(f"cat {path} 2>/dev/null")
            if exit_code == 0 and stdout.strip():
                mac = stdout.strip().lower()
                if re.match(r"^[0-9a-f:]{17}$", mac):
                    return mac

        # Method 2: Get MAC of the mesh hard interface(s)
        # List all interfaces that are part of this batman mesh
        stdout, _, exit_code = connection.execute(
            f"cat /sys/class/net/{bat_iface}/lower_*/address 2>/dev/null"
        )
        if exit_code == 0 and stdout.strip():
            # Use the first hard interface's MAC as the originator
            for line in stdout.strip().split("\n"):
                mac = line.strip().lower()
                if re.match(r"^[0-9a-f:]{17}$", mac):
                    return mac

        # Method 3: Use batctl to get the list of hard interfaces
        for cmd in [
            f"batctl meshif {bat_iface} if 2>/dev/null",
            f"batctl -m {bat_iface} if 2>/dev/null",
            "batctl if 2>/dev/null",
        ]:
            stdout, _, exit_code = connection.execute(cmd)
            if exit_code == 0 and stdout.strip():
                # Format: "wlan0-mesh: active" or "mesh0: active"
                for line in stdout.split("\n"):
                    if "active" in line:
                        parts = line.split(":")
                        if parts:
                            hardif = parts[0].strip()
                            # Get MAC of this interface
                            stdout2, _, exit_code2 = connection.execute(
                                f"cat /sys/class/net/{hardif}/address 2>/dev/null"
                            )
                            if exit_code2 == 0 and stdout2.strip():
                                mac = stdout2.strip().lower()
                                if re.match(r"^[0-9a-f:]{17}$", mac):
                                    return mac
                break

        # Method 4: Fall back to bat0 interface MAC itself
        stdout, _, exit_code = connection.execute(
            f"cat /sys/class/net/{bat_iface}/address 2>/dev/null"
        )
        if exit_code == 0 and stdout.strip():
            return stdout.strip().lower()

    return None


def _collect_node_raw_data(connection: SSHConnection) -> _NodeRawData:
    """
    Collect raw data from a node (WiFi clients, ARP, DHCP, bridge FDB, batman).

    This is an internal function that collects data without deduplication.
    """
    hostname = _get_hostname(connection)
    interface_ssids = _get_interface_ssids(connection)
    wifi_interfaces = _get_wireless_interfaces(connection)

    # Collect DHCP leases (for IP and hostname lookup)
    stdout, _, _ = connection.execute("cat /tmp/dhcp.leases 2>/dev/null")
    dhcp_leases = _parse_dhcp_leases(stdout)

    # Collect ARP table (for IP lookup of non-DHCP clients)
    stdout, _, _ = connection.execute("cat /proc/net/arp")
    arp_table = _parse_arp_table(stdout)

    # Collect bridge forwarding database (to know which port clients are on)
    bridge_fdb = _get_bridge_port_mapping(connection)

    # Collect BATMAN-ADV translation table (to know which node a client is behind)
    batman_tt = _get_batman_translation_table(connection)
    node_mac = _get_node_batman_mac(connection)

    wifi_clients: List[Client] = []

    # Collect WiFi clients from each wireless interface
    for iface in wifi_interfaces:
        stdout, _, exit_code = connection.execute(f"iw dev {iface} station dump")
        if exit_code != 0:
            continue

        stations = _parse_wifi_stations(stdout, iface)
        ssid = interface_ssids.get(iface)

        for station in stations:
            lease = dhcp_leases.get(station.mac)

            wifi_clients.append(
                Client(
                    mac=station.mac,
                    ip=lease.ip if lease else arp_table.get(station.mac),
                    hostname=lease.hostname if lease else None,
                    connection_type="wifi",
                    interface=iface,
                    ssid=ssid,
                    signal=station.signal,
                    inactive_ms=station.inactive_ms,
                    tx_bitrate=station.tx_bitrate,
                    rx_bitrate=station.rx_bitrate,
                )
            )

    return _NodeRawData(
        host=connection.host,
        hostname=hostname,
        interface_ssids=interface_ssids,
        wifi_clients=wifi_clients,
        arp_table=arp_table,
        dhcp_leases=dhcp_leases,
        bridge_fdb=bridge_fdb,
        batman_tt=batman_tt,
        node_mac=node_mac,
    )


def collect_node_info(connection: SSHConnection) -> MeshNode:
    """
    Collect information about clients connected to a single node.

    Note: When collecting a single node, LAN clients from ARP table are included.
    For mesh networks, use collect_mesh_network() which handles deduplication.

    Args:
        connection: Active SSH connection to the node

    Returns:
        MeshNode with all connected clients
    """
    raw = _collect_node_raw_data(connection)

    clients = list(raw.wifi_clients)
    wifi_macs = {c.mac for c in raw.wifi_clients}

    # Add LAN clients (from bridge FDB, excluding WiFi clients)
    # Use bridge FDB to get the actual interface they're connected to
    for mac, ip in raw.arp_table.items():
        if mac not in wifi_macs:
            # Get the physical port from bridge FDB
            interface = raw.bridge_fdb.get(mac, "br-lan")
            lease = raw.dhcp_leases.get(mac)
            clients.append(
                Client(
                    mac=mac,
                    ip=ip,
                    hostname=lease.hostname if lease else None,
                    connection_type="lan",
                    interface=interface,
                    ssid=None,
                    signal=None,
                )
            )

    return MeshNode(
        host=connection.host,
        hostname=raw.hostname,
        clients=clients,
        interfaces=raw.interface_ssids,
    )


def collect_mesh_network(
    main_host: str,
    node_hosts: Optional[List[str]] = None,
    username: str = "root",
    password: Optional[str] = None,
    key_filename: Optional[str] = None,
    port: int = 22,
    timeout: int = 30,
    include_stale: bool = True,
) -> MeshNetwork:
    """
    Collect information about an entire mesh network.

    This function handles deduplication:
    - WiFi clients are only shown on the node they're connected to
    - LAN clients are shown on the node where they're physically connected
      (determined via bridge forwarding database)
    - Clients seen in ARP but coming through mesh backhaul are excluded

    Args:
        main_host: IP/hostname of the main router (runs DHCP server)
        node_hosts: List of IP/hostnames of mesh nodes (optional)
        username: SSH username (default: root)
        password: SSH password
        key_filename: Path to SSH private key
        port: SSH port (default: 22)
        timeout: Connection timeout in seconds
        include_stale: Include LAN clients that have no bridge FDB entry (likely stale ARP entries).
                       Set to False to only show clients with confirmed physical presence.

    Returns:
        MeshNetwork containing all nodes and their clients
    """
    all_hosts = [main_host] + (node_hosts or [])
    raw_data: List[Optional[_NodeRawData]] = []
    errors: Dict[str, str] = {}

    # Phase 1: Collect raw data from all nodes
    for host in all_hosts:
        try:
            connection = SSHConnection(
                host=host,
                port=port,
                username=username,
                password=password,
                key_filename=key_filename,
                timeout=timeout,
            )
            with connection:
                raw_data.append(_collect_node_raw_data(connection))
        except Exception as e:
            raw_data.append(None)
            errors[host] = str(e)

    # Phase 2: Collect all WiFi MACs from all nodes (for deduplication)
    all_wifi_macs: set = set()
    # Also collect DHCP leases from main router for enrichment
    main_dhcp_leases: Dict[str, DHCPLease] = {}
    # Track which MACs have been assigned as LAN clients (to prevent duplicates)
    assigned_lan_macs: set = set()

    for idx, raw in enumerate(raw_data):
        if raw is None:
            continue
        for client in raw.wifi_clients:
            all_wifi_macs.add(client.mac)
        # Main router (first host) has the DHCP leases
        if idx == 0:
            main_dhcp_leases = raw.dhcp_leases

    # Build mapping of batman originator MAC -> node index
    # This lets us determine which node a client is behind using batman TT
    originator_to_node_idx: Dict[str, int] = {}
    originator_to_hostname: Dict[str, str] = {}
    for idx, raw in enumerate(raw_data):
        if raw is None:
            continue
        if raw.node_mac:
            originator_to_node_idx[raw.node_mac] = idx
            originator_to_hostname[raw.node_mac] = raw.hostname

    # Get batman translation table from main router (most complete view)
    main_batman_tt: Dict[str, str] = {}
    if raw_data[0] is not None:
        main_batman_tt = raw_data[0].batman_tt

    # Pre-compute which node each LAN MAC belongs to
    # Priority: 1) batman TT, 2) FDB on physical LAN port, 3) local FDB
    mac_to_node_idx: Dict[str, int] = {}
    mac_to_via_node: Dict[str, str] = {}  # For display: which node name the client is behind
    mac_to_ip: Dict[str, str] = {}  # Collect all MAC->IP mappings for later use

    # First pass: Collect all ARP entries and assign based on batman TT
    for idx, raw in enumerate(raw_data):
        if raw is None:
            continue
        # Collect all MAC->IP mappings
        for mac, ip in raw.arp_table.items():
            if mac not in mac_to_ip:
                mac_to_ip[mac] = ip

    # Second pass: Determine node assignment for each LAN MAC
    for mac in mac_to_ip.keys():
        if mac in all_wifi_macs:
            continue
        if mac in mac_to_node_idx:
            continue

        # Method 1: Check batman translation table (highest priority)
        originator_mac = main_batman_tt.get(mac)
        if originator_mac and originator_mac in originator_to_node_idx:
            target_idx = originator_to_node_idx[originator_mac]
            mac_to_node_idx[mac] = target_idx
            mac_to_via_node[mac] = originator_to_hostname.get(originator_mac, originator_mac)
            continue

        # Method 2: Check each node's FDB for this MAC on a physical port
        for idx, raw in enumerate(raw_data):
            if raw is None:
                continue
            if mac in raw.bridge_fdb:
                device = raw.bridge_fdb[mac]
                wifi_ifaces = list(raw.interface_ssids.keys())
                # Skip if on wifi or mesh interface
                if device in wifi_ifaces:
                    continue
                if any(p in device.lower() for p in ["bat", "mesh", "wds"]):
                    continue
                # This MAC is on a physical port on this node
                mac_to_node_idx[mac] = idx
                break

    # Phase 3: Build nodes with deduplicated clients
    nodes: List[MeshNode] = []

    for idx, host in enumerate(all_hosts):
        raw = raw_data[idx]

        if raw is None:
            nodes.append(
                MeshNode(
                    host=host,
                    hostname=f"(connection failed: {errors.get(host, 'unknown')})",
                    clients=[],
                    interfaces={},
                )
            )
            continue

        clients: List[Client] = []

        # Add WiFi clients (enrich with main router's DHCP data if needed)
        for client in raw.wifi_clients:
            # Try to enrich with DHCP data from main router
            if not client.ip or not client.hostname:
                lease = main_dhcp_leases.get(client.mac)
                if lease:
                    clients.append(
                        Client(
                            mac=client.mac,
                            ip=client.ip or lease.ip,
                            hostname=client.hostname or lease.hostname,
                            connection_type=client.connection_type,
                            interface=client.interface,
                            ssid=client.ssid,
                            signal=client.signal,
                            inactive_ms=client.inactive_ms,
                            tx_bitrate=client.tx_bitrate,
                            rx_bitrate=client.rx_bitrate,
                        )
                    )
                else:
                    clients.append(client)
            else:
                clients.append(client)

        # Add LAN clients that are physically connected to THIS node
        # We iterate over all known LAN MACs (from mac_to_ip collected earlier)
        for mac, ip in mac_to_ip.items():
            if mac in all_wifi_macs:
                # Already shown as WiFi client
                continue

            if mac in assigned_lan_macs:
                # Already assigned to another node
                continue

            # Check if this MAC should be assigned to this node
            should_include = False
            is_stale = mac not in mac_to_node_idx  # No FDB/batman entry = likely stale

            if mac in mac_to_node_idx:
                # We have assignment data - only include if this is the right node
                should_include = mac_to_node_idx[mac] == idx
            elif include_stale and idx == 0:
                # No assignment data for this MAC on any node
                # Assign to main router (idx 0) as fallback, but only if include_stale is True
                should_include = True

            if should_include:
                # Determine interface - prefer this node's FDB, fallback to main router's
                interface = raw.bridge_fdb.get(mac)
                if not interface and raw_data[0] is not None:
                    interface = raw_data[0].bridge_fdb.get(mac, "br-lan")
                if not interface:
                    interface = "br-lan"
                lease = main_dhcp_leases.get(mac) or raw.dhcp_leases.get(mac)
                # Get via_node info if this client was identified via batman TT
                via_node = mac_to_via_node.get(mac)
                clients.append(
                    Client(
                        mac=mac,
                        ip=ip,
                        hostname=lease.hostname if lease else None,
                        connection_type="lan",
                        interface=interface,
                        ssid=None,
                        signal=None,
                        via_node=via_node,
                        stale=is_stale,
                    )
                )
                assigned_lan_macs.add(mac)

        nodes.append(
            MeshNode(
                host=raw.host,
                hostname=raw.hostname,
                clients=clients,
                interfaces=raw.interface_ssids,
            )
        )

    return MeshNetwork(nodes=nodes)


def display_mesh_tree(network: MeshNetwork, use_color: bool = False) -> str:
    """
    Display the mesh network as an ASCII tree.

    Args:
        network: The MeshNetwork to display
        use_color: Whether to use ANSI color codes (default: False)

    Returns:
        String representation of the network tree
    """
    # ANSI color codes
    CYAN = "\033[36m" if use_color else ""
    GREEN = "\033[32m" if use_color else ""
    YELLOW = "\033[33m" if use_color else ""
    MAGENTA = "\033[35m" if use_color else ""
    RESET = "\033[0m" if use_color else ""

    lines: List[str] = []
    lines.append(f"{CYAN}Mesh Network{RESET}")

    for node_idx, node in enumerate(network.nodes):
        is_last_node = node_idx == len(network.nodes) - 1
        node_prefix = "└── " if is_last_node else "├── "
        child_prefix = "    " if is_last_node else "│   "

        # Node header
        node_name = f"{node.host}"
        if node.hostname:
            node_name += f" ({GREEN}{node.hostname}{RESET})"
        lines.append(f"{node_prefix}{node_name}")

        # Group clients by connection type and SSID/interface
        wifi_by_ssid: Dict[str, List[Client]] = {}
        lan_by_port: Dict[str, List[Client]] = {}

        for client in node.clients:
            if client.connection_type == "wifi":
                ssid = client.ssid or "(unknown SSID)"
                if ssid not in wifi_by_ssid:
                    wifi_by_ssid[ssid] = []
                wifi_by_ssid[ssid].append(client)
            else:
                # Group LAN clients by their physical port/interface
                port = client.interface or "br-lan"
                if port not in lan_by_port:
                    lan_by_port[port] = []
                lan_by_port[port].append(client)

        # Build groups list: WiFi SSIDs first, then LAN ports
        groups: List[tuple] = []  # (type, name, clients)
        for ssid in sorted(wifi_by_ssid.keys()):
            groups.append(("wifi", ssid, wifi_by_ssid[ssid]))
        for port in sorted(lan_by_port.keys()):
            groups.append(("lan", port, lan_by_port[port]))

        # If no clients at all, show empty LAN section
        if not groups:
            groups.append(("lan", "LAN", []))

        for group_idx, (group_type, group_name, clients_list) in enumerate(groups):
            is_last_group = group_idx == len(groups) - 1
            group_prefix = "└── " if is_last_group else "├── "
            client_prefix = "    " if is_last_group else "│   "

            if group_type == "lan":
                # Show actual port name (e.g., lan1, lan2, eth0)
                display_name = group_name if group_name != "br-lan" else "LAN"
                lines.append(f"{child_prefix}{group_prefix}{YELLOW}[LAN: {display_name}]{RESET}")
            else:
                lines.append(f"{child_prefix}{group_prefix}{MAGENTA}[WiFi: {group_name}]{RESET}")

            if not clients_list:
                lines.append(f"{child_prefix}{client_prefix}└── (no clients)")
            else:
                for client_idx, client in enumerate(clients_list):
                    is_last_client = client_idx == len(clients_list) - 1
                    client_line_prefix = "└── " if is_last_client else "├── "

                    # Format client info
                    client_info = client.mac.upper()
                    if client.ip:
                        client_info += f" - {client.ip}"
                    if client.hostname:
                        client_info += f" ({client.hostname})"

                    # WiFi-specific info: signal, bitrate, inactive time
                    if client.connection_type == "wifi":
                        if client.signal is not None:
                            client_info += f" {client.signal}dBm"
                        if client.tx_bitrate:
                            client_info += f" TX:{client.tx_bitrate}"
                        if client.inactive_ms is not None:
                            # Format inactive time nicely
                            if client.inactive_ms < 1000:
                                client_info += f" idle:{client.inactive_ms}ms"
                            elif client.inactive_ms < 60000:
                                client_info += f" idle:{client.inactive_ms // 1000}s"
                            else:
                                mins = client.inactive_ms // 60000
                                client_info += f" idle:{mins}m"

                    # Mesh node attribution
                    if client.via_node:
                        client_info += f" [via {client.via_node}]"

                    # Mark stale clients
                    if client.stale:
                        DIM = "\033[2m" if use_color else ""
                        client_info = f"{DIM}(stale) {client_info}{RESET}"

                    lines.append(f"{child_prefix}{client_prefix}{client_line_prefix}{client_info}")

    return "\n".join(lines)
