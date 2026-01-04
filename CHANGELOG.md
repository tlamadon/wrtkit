# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Remote Policy Whitelist**: New whitelist-based approach for selectively preserving remote settings
  - Path glob patterns (e.g., `interfaces.*.gateway`, `devices.br_lan.*`)
  - Support for `*` (single segment) and `**` (multi-segment) wildcards
  - Patterns ending with `.*` automatically include section definitions
  - Logical path hierarchy (devices, interfaces, hosts, radios, etc.)
- **Enhanced Diff Display**: Whitelisted items now tracked separately and hidden by default
  - New `diff.whitelisted` list for preserved remote settings
  - Summary now shows: "5 whitelisted, 3 in common"
  - Cleaner output focused on actual changes
- Comprehensive documentation in `REMOTE_POLICY_WHITELIST.md`
- Example configurations and demos

### Changed
- `ConfigDiff` now has separate `whitelisted` field (previously mixed with `remote_only`)
- Remote policy now uses `should_keep_remote_path()` as primary method
- Diff output only shows items that will change (whitelisted items hidden like common items)

### Deprecated
- `RemotePolicy.allowed_sections` - Use `whitelist` instead
- `RemotePolicy.allowed_values` - Use `whitelist` instead
- Legacy methods still supported for backward compatibility

## [0.1.0] - 2025-01-XX

### Added
- Initial release of WRTKit
- Core UCI configuration model with builder pattern
- Network configuration support
  - Network devices (bridges, VLANs)
  - Network interfaces (static, DHCP, batman-adv)
- Wireless configuration support
  - Radio configuration
  - WiFi interfaces (AP, mesh, station modes)
  - 802.11r fast roaming support
- DHCP server configuration support
- Firewall configuration support
  - Zones
  - Forwarding rules
- SSH connection management
  - Password and key-based authentication
  - Remote command execution
  - UCI command helpers
- Configuration diff functionality
  - Compare local configuration with remote device
  - Display differences in human-readable format
- Configuration apply functionality
  - Apply configurations to remote devices
  - Dry-run mode
  - Automatic commit and reload options
- Export to shell scripts
- Comprehensive examples
- Test suite
- Documentation

[Unreleased]: https://github.com/yourusername/wrtkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/wrtkit/releases/tag/v0.1.0
