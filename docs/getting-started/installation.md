# Installation

## Requirements

- Python 3.8 or higher
- pip package manager

## Install from PyPI

The easiest way to install WRTKit is using pip:

```bash
pip install wrtkit
```

## Install from Source

To install the latest development version from source:

```bash
git clone https://github.com/yourusername/wrtkit.git
cd wrtkit
pip install -e .
```

## Development Installation

If you want to contribute to WRTKit, install it with development dependencies:

```bash
git clone https://github.com/yourusername/wrtkit.git
cd wrtkit
pip install -e ".[dev]"
```

This installs additional tools for testing, linting, and type checking:

- pytest - Testing framework
- pytest-cov - Coverage reporting
- black - Code formatting
- ruff - Linting
- mypy - Type checking

## Verify Installation

Verify that WRTKit is installed correctly:

```python
import wrtkit
print(wrtkit.__version__)
```

Or run a simple test:

```python
from wrtkit import UCIConfig

config = UCIConfig()
config.network.interface("test").device("eth0").proto("static")
print(config.to_script())
```

You should see UCI commands printed to the console.

## Dependencies

WRTKit has minimal runtime dependencies:

- **paramiko** (>=3.0.0) - SSH client library for remote operations

All dependencies are automatically installed when you install WRTKit via pip.

## Next Steps

Now that you have WRTKit installed, proceed to the [Quick Start](quick-start.md) guide to create your first configuration.
