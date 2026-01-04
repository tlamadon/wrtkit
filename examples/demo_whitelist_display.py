"""
Demo showing the new whitelisted display in diff output.

This demonstrates how whitelisted items are now counted separately
and not shown in the tree view by default (like common items).
"""

from wrtkit import UCIConfig, NetworkInterface, RemotePolicy


class MockSSH:
    """Mock SSH connection for demo purposes."""

    def get_uci_config(self, package: str) -> str:
        if package == "network":
            return """
network.lan=interface
network.lan.proto='static'
network.lan.ipaddr='192.168.1.1'
network.lan.gateway='192.168.1.254'
network.lan.dns='8.8.8.8'
network.guest=interface
network.guest.proto='static'
network.guest.ipaddr='192.168.100.1'
network.guest.gateway='192.168.100.254'
network.temp=interface
network.temp.proto='dhcp'
"""
        return ""


# Create local config - only manage LAN interface basics
config = UCIConfig()
lan = NetworkInterface("lan").with_proto("static").with_ipaddr("192.168.1.1")
config.network.add_interface(lan)

# Configure whitelist to preserve some remote settings
config.network.remote_policy = RemotePolicy(
    whitelist=[
        "interfaces.*.gateway",  # Keep gateway on all interfaces
        "interfaces.guest.*",  # Keep entire guest interface
    ]
)

# Get the diff
diff = config.diff(MockSSH(), show_remote_only=True)

print("=" * 70)
print("TREE VIEW (whitelisted items not shown, only counted)")
print("=" * 70)
print(diff.to_tree(color=True))

print("\n\n" + "=" * 70)
print("WHAT HAPPENED:")
print("=" * 70)
print(f"""
Local config defines:
  - network.lan with proto='static' and ipaddr='192.168.1.1'

Remote has:
  - network.lan with proto, ipaddr, gateway, dns
  - network.guest with proto, ipaddr, gateway (entire interface)
  - network.temp with proto (entire interface)

Whitelist patterns:
  - interfaces.*.gateway  → Preserves gateway on any interface
  - interfaces.guest.*    → Preserves all guest interface settings

Results:
  ✓ In common (matched): {len(diff.common)} items
    - network.lan (section def)
    - network.lan.proto
    - network.lan.ipaddr

  ✓ Whitelisted (preserved): {len(diff.whitelisted)} items
    - network.lan.gateway     (matches interfaces.*.gateway)
    - network.guest           (matches interfaces.guest.*)
    - network.guest.proto     (matches interfaces.guest.*)
    - network.guest.ipaddr    (matches interfaces.guest.*)
    - network.guest.gateway   (matches interfaces.guest.*)

  ✗ To remove: {len(diff.to_remove)} items
    - network.lan.dns         (not whitelisted)
    - network.temp            (not whitelisted)
    - network.temp.proto      (not whitelisted)

Note: Whitelisted items are NOT displayed in the tree view (like common items),
they're only counted in the summary. This keeps the output focused on what
will actually change.
""")

print("\n" + "=" * 70)
print("SUMMARY BREAKDOWN:")
print("=" * 70)
print(f"""
Common items:       {len(diff.common):3d}  (in both, identical - not shown)
Whitelisted items:  {len(diff.whitelisted):3d}  (remote-only but preserved - not shown)
To add:             {len(diff.to_add):3d}  (in local, not on remote - SHOWN)
To modify:          {len(diff.to_modify):3d}  (different values - SHOWN)
To remove:          {len(diff.to_remove):3d}  (remote-only, not whitelisted - SHOWN)
Remote-only:        {len(diff.remote_only):3d}  (no policy, won't be deleted - SHOWN)
""")

print("\nThis makes the diff output much cleaner - you only see what will")
print("actually change, while whitelisted items are quietly preserved!")
