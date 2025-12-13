# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
