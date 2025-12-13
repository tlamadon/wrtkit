# Testing

WRTKit includes a comprehensive test suite to ensure reliability.

## Running Tests

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=wrtkit --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Test a specific file
pytest tests/test_network.py

# Test a specific function
pytest tests/test_network.py::test_device_creation

# Test a specific class
pytest tests/test_config.py::TestUCIConfig
```

## Test Structure

```
tests/
├── __init__.py
├── test_config.py      # Main configuration tests
├── test_network.py     # Network configuration tests
├── test_wireless.py    # Wireless configuration tests
├── test_dhcp.py        # DHCP configuration tests
└── test_firewall.py    # Firewall configuration tests
```

## Writing Tests

### Basic Test

```python
def test_network_interface():
    from wrtkit import UCIConfig

    config = UCIConfig()
    config.network.interface("lan") \
        .device("eth0") \
        .proto("static") \
        .ipaddr("192.168.1.1")

    commands = config.get_all_commands()

    assert len(commands) > 0
    assert any("network.lan.ipaddr" in cmd.path for cmd in commands)
```

### Test with Assertions

```python
def test_wireless_configuration():
    from wrtkit.wireless import WirelessConfig
    from wrtkit.base import UCICommand

    wireless = WirelessConfig()
    wireless.radio("radio0").channel(11).htmode("HT20")

    commands = wireless.get_commands()

    assert commands[0] == UCICommand("set", "wireless.radio0", "wifi-device")
    assert any(cmd.path == "wireless.radio0.channel" and cmd.value == "11"
               for cmd in commands)
```

## Code Quality

### Linting

```bash
ruff check src/ tests/ examples/
```

### Code Formatting

```bash
black src/ tests/ examples/
```

### Type Checking

```bash
mypy src/wrtkit
```

## Continuous Integration

Tests run automatically on:
- Every push to main
- Every pull request
- Multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)

See the GitHub Actions workflow in `.github/workflows/docs.yml` for CI configuration.

## See Also

- [Contributing](contributing.md) - Contribution guidelines
- [Publishing](publishing.md) - Publishing to PyPI
