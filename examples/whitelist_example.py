"""
Example demonstrating the new whitelist-based remote_policy feature.

This example shows how to use path glob patterns to selectively preserve
remote configuration settings.
"""

from wrtkit import UCIConfig, NetworkInterface, RemotePolicy

# Create a configuration
config = UCIConfig()

# Define only the LAN interface in local config
lan = (
    NetworkInterface("lan")
    .with_proto("static")
    .with_ipaddr("192.168.1.1")
    .with_netmask("255.255.255.0")
)
config.network.add_interface(lan)

# Configure remote policy with whitelist patterns
# This will preserve specific remote settings that aren't in local config
config.network.remote_policy = RemotePolicy(
    whitelist=[
        "interfaces.*.gateway",  # Keep gateway setting on all interfaces
        "interfaces.guest.*",  # Keep entire guest interface (all options)
        "interfaces.vpn.*",  # Keep entire vpn interface (all options)
        "devices.*.ports",  # Keep all ports on all devices
    ]
)

print("Remote Policy Whitelist Configuration")
print("=" * 60)
print("\nLocal Configuration:")
print("  - LAN interface with static IP 192.168.1.1")
print("\nWhitelist Patterns:")
for pattern in config.network.remote_policy.whitelist:
    print(f"  - {pattern}")

print("\n\nWhat this means:")
print("-" * 60)
print("1. LAN Gateway:")
print("   If remote has 'gateway' set on LAN, it will be PRESERVED")
print("   even though it's not in local config")
print()
print("2. Guest Interface:")
print("   If remote has a 'guest' interface, ALL of its settings")
print("   will be PRESERVED (proto, ipaddr, netmask, etc.)")
print()
print("3. VPN Interface:")
print("   If remote has a 'vpn' interface, ALL of its settings")
print("   will be PRESERVED")
print()
print("4. Device Ports:")
print("   If remote has devices with 'ports' configured, those")
print("   ports will be PRESERVED (e.g., bat0, wlan0 on bridges)")
print()
print("5. Everything Else:")
print("   Any remote-only settings NOT matching the patterns")
print("   will be REMOVED when syncing")

# Example: Test the pattern matching
print("\n\nPattern Matching Examples:")
print("-" * 60)

test_paths = [
    ("interfaces.lan.gateway", "KEEP - matches interfaces.*.gateway"),
    ("interfaces.wan.gateway", "KEEP - matches interfaces.*.gateway"),
    ("interfaces.guest.proto", "KEEP - matches interfaces.guest.*"),
    ("interfaces.guest.ipaddr", "KEEP - matches interfaces.guest.*"),
    ("interfaces.vpn.device", "KEEP - matches interfaces.vpn.*"),
    ("devices.br_lan.ports", "KEEP - matches devices.*.ports"),
    ("interfaces.temp.proto", "REMOVE - no pattern matches"),
    ("devices.br_lan.type", "REMOVE - no pattern matches"),
]

for path, expected in test_paths:
    is_kept = config.network.remote_policy.is_path_whitelisted(path)
    status = "✓ KEEP" if is_kept else "✗ REMOVE"
    print(f"  {status}  {path:30s} - {expected}")

# Additional examples with different patterns
print("\n\nOther Useful Whitelist Patterns:")
print("-" * 60)

examples = {
    "Keep everything": ["**"],
    "Keep all devices": ["devices.*"],
    "Keep specific interface options": [
        "interfaces.lan.gateway",
        "interfaces.lan.dns",
    ],
    "Keep DHCP hostnames": ["hosts.*.hostname"],
    "Keep WiFi radios": ["radios.*"],
    "Keep firewall zones": ["zones.*"],
}

for description, patterns in examples.items():
    print(f"\n{description}:")
    for pattern in patterns:
        print(f"  - {pattern}")

# Legacy approach for comparison
print("\n\nLegacy Approach (Deprecated):")
print("-" * 60)
print("Old way using allowed_sections and allowed_values:")
print("""
network:
  remote_policy:
    allowed_sections:
      - "lan"
      - "guest"
      - "vpn"
    allowed_values:
      - "lan*"
""")

print("\nNew way using whitelist (more precise):")
print("""
network:
  remote_policy:
    whitelist:
      - "interfaces.*.gateway"
      - "interfaces.guest.*"
      - "interfaces.vpn.*"
      - "devices.*.ports"
""")

print("\n\nKey Advantages of Whitelist Approach:")
print("-" * 60)
print("1. More precise control - specify exact paths")
print("2. Easier to understand - paths show exactly what's kept")
print("3. Can preserve specific options in locally-managed sections")
print("4. Supports glob patterns at any level")
print("5. Single unified approach instead of two separate lists")
