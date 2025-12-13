# WRTKit Project Summary

## Overview

WRTKit is a Python library for managing OpenWRT configuration over SSH. It provides a declarative, builder-pattern API for defining UCI (Unified Configuration Interface) configurations in Python, comparing them with remote devices, and applying changes.

## Project Structure

```
wrtkit/
├── src/wrtkit/              # Main library code
│   ├── __init__.py          # Package exports
│   ├── base.py              # Base classes (UCICommand, UCISection, BaseBuilder)
│   ├── config.py            # Main UCIConfig class and diff/apply logic
│   ├── ssh.py               # SSH connection management
│   ├── network.py           # Network configuration (devices, interfaces)
│   ├── wireless.py          # Wireless configuration (radios, wifi interfaces)
│   ├── dhcp.py              # DHCP server configuration
│   └── firewall.py          # Firewall zones and forwarding rules
│
├── tests/                   # Test suite (18 tests, all passing)
│   ├── test_config.py       # Tests for main config and UCI commands
│   ├── test_network.py      # Tests for network configuration
│   ├── test_wireless.py     # Tests for wireless configuration
│   ├── test_dhcp.py         # Tests for DHCP configuration
│   └── test_firewall.py     # Tests for firewall configuration
│
├── examples/                # Usage examples
│   ├── simple_example.py    # Basic router setup
│   ├── router_config.py     # Advanced mesh network (mirrors uci/router.cfg)
│   └── README.md            # Examples documentation
│
├── uci/                     # Reference configurations
│   └── router.cfg           # Original UCI configuration (reference)
│
├── .github/workflows/       # CI/CD
│   ├── docs.yml             # CI workflow (test, lint, type check)
│   └── publish.yml          # PyPI publishing workflow
│
└── Documentation
    ├── README.md            # Main documentation
    ├── GETTING_STARTED.md   # Quick start guide
    ├── CONTRIBUTING.md      # Contribution guidelines
    ├── PUBLISHING.md        # PyPI publishing instructions
    ├── CHANGELOG.md         # Version history
    └── LICENSE              # MIT License
```

## Core Architecture

### 1. Builder Pattern

The library uses a fluent builder pattern for easy configuration:

```python
config.network.interface("lan") \
    .device("eth0") \
    .proto("static") \
    .ipaddr("192.168.1.1")
```

### 2. UCI Command Generation

Everything is internally represented as `UCICommand` objects:
- `UCICommand("set", "network.lan", "interface")`
- `UCICommand("set", "network.lan.device", "eth0")`
- `UCICommand("add_list", "network.br_lan.ports", "lan1")`

### 3. Configuration Management

**UCIConfig** is the main entry point that manages:
- `network`: NetworkConfig (devices, interfaces)
- `wireless`: WirelessConfig (radios, wifi interfaces)
- `dhcp`: DHCPConfig (DHCP servers)
- `firewall`: FirewallConfig (zones, forwarding)

### 4. SSH Integration

**SSHConnection** provides:
- Connection management (password or key-based auth)
- Remote command execution
- UCI configuration retrieval
- Commit and reload operations

### 5. Diff and Apply

- `config.diff(ssh)`: Compare local config with remote device
- `config.apply(ssh)`: Apply configuration to remote device
- `config.to_script()`: Generate shell script
- `config.save_to_file()`: Save to file

## Features

### Supported UCI Components

#### Network
- Devices: bridges, VLANs (8021q)
- Interfaces: static IP, DHCP client, batman-adv, batman-adv hardif
- Options: IP address, netmask, gateway, MTU, routing algorithms

#### Wireless
- Radio configuration: channel, HT mode, country code, TX power
- WiFi interfaces: AP, mesh, station modes
- Security: WPA2-PSK, WPA3-SAE
- 802.11r fast roaming support

#### DHCP
- DHCP server configuration
- IP range (start, limit)
- Lease time
- Enable/disable per interface

#### Firewall
- Zone configuration (input/output/forward policies)
- Forwarding rules between zones
- Masquerading and MTU fix
- Multi-network zones

## Key Design Decisions

1. **Immutable Commands**: UCI commands are generated from configuration objects, not modified in place

2. **Type Safety**: Uses Python type hints throughout for better IDE support and type checking

3. **Modular Design**: Each UCI package (network, wireless, etc.) is in its own module

4. **Builder Pattern**: Fluent interface for easy configuration chaining

5. **Test Coverage**: Comprehensive test suite covering all major functionality

## Usage Patterns

### 1. Generate Script Only
```python
config = UCIConfig()
# ... configure ...
config.save_to_file("config.sh")
```

### 2. Compare with Remote
```python
ssh = SSHConnection("192.168.1.1", username="root", password="secret")
diff = config.diff(ssh)
print(diff)
```

### 3. Apply to Remote
```python
with SSHConnection(...) as ssh:
    diff = config.diff(ssh)
    if not diff.is_empty():
        config.apply(ssh, auto_commit=True, auto_reload=True)
```

### 4. Dry Run
```python
config.apply(ssh, dry_run=True)  # Show what would be executed
```

## Publishing to PyPI

The project is ready to be published to PyPI:

1. Update `pyproject.toml` with your information
2. Follow instructions in `PUBLISHING.md`
3. Use GitHub Actions for automated publishing (on tag push)
4. Or manually: `python -m build && twine upload dist/*`

## Development Workflow

```bash
# Setup
git clone <repo>
cd wrtkit
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=wrtkit --cov-report=html

# Code quality
black src/ tests/ examples/
ruff check src/ tests/ examples/
mypy src/wrtkit

# Run examples
python examples/simple_example.py
python examples/router_config.py
```

## Dependencies

**Runtime:**
- `paramiko>=3.0.0` - SSH client for remote connections

**Development:**
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.0.0` - Type checking

## Future Enhancements

Potential areas for expansion:

1. **More UCI Packages**: system, dropbear, luci, etc.
2. **Configuration Validation**: Pre-apply validation of configuration
3. **Rollback Support**: Automatic rollback on failure
4. **Configuration Templates**: Pre-built templates for common setups
5. **CLI Tool**: Command-line interface for quick operations
6. **Documentation Site**: Full API documentation with mkdocs
7. **More Protocols**: Support for more network protocols and features

## Testing

- 18 tests covering all major functionality
- All tests passing
- Test organization by UCI package
- Integration-ready (SSH tests would require live router)

## License

MIT License - Free for commercial and non-commercial use
