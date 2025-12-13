# Contributing to WRTKit

Thank you for your interest in contributing to WRTKit!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wrtkit.git
cd wrtkit
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

## Running Tests

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=wrtkit --cov-report=html
```

## Code Style

This project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Format your code:
```bash
black src/ tests/ examples/
```

Run linting:
```bash
ruff check src/ tests/ examples/
```

Run type checking:
```bash
mypy src/
```

## Adding New Features

1. Create a new branch for your feature
2. Write tests for your feature
3. Implement the feature
4. Ensure all tests pass
5. Format and lint your code
6. Submit a pull request

## Adding New UCI Components

To add support for a new UCI package (e.g., system, firewall rules):

1. Create a new module in `src/wrtkit/` (e.g., `system.py`)
2. Define section classes inheriting from `UCISection`
3. Create builder classes inheriting from `BaseBuilder`
4. Create a config manager class
5. Add the new config to `UCIConfig` in `config.py`
6. Write tests in `tests/`
7. Add examples in `examples/`

## Documentation

When adding new features, please update:
- Docstrings in the code
- README.md if needed
- Example files
- CHANGELOG.md

## Questions?

Feel free to open an issue for any questions or concerns.
