# Publishing WRTKit to PyPI

This guide explains how to publish the wrtkit package to PyPI.

## Prerequisites

1. Create accounts on:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)

2. Install build tools:
```bash
pip install build twine
```

## Before Publishing

1. **Update version** in `pyproject.toml`:
```toml
version = "0.1.0"  # Update this
```

2. **Update author information** in `pyproject.toml`:
```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
```

3. **Update URLs** in `pyproject.toml`:
```toml
[project.urls]
Homepage = "https://github.com/yourusername/wrtkit"
Repository = "https://github.com/yourusername/wrtkit"
```

4. **Run tests**:
```bash
pytest
```

5. **Check code quality**:
```bash
black src/ tests/ examples/
ruff check src/ tests/ examples/
mypy src/
```

## Building the Package

Build the distribution packages:
```bash
python -m build
```

This creates:
- `dist/wrtkit-0.1.0.tar.gz` (source distribution)
- `dist/wrtkit-0.1.0-py3-none-any.whl` (wheel distribution)

## Testing on TestPyPI

1. Upload to TestPyPI:
```bash
python -m twine upload --repository testpypi dist/*
```

2. Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ wrtkit
```

3. Test the installed package:
```bash
python -c "from wrtkit import UCIConfig; print('Success!')"
```

## Publishing to PyPI

Once you've verified everything works on TestPyPI:

1. Upload to PyPI:
```bash
python -m twine upload dist/*
```

2. Install from PyPI:
```bash
pip install wrtkit
```

## Using GitHub Actions for Automated Publishing

The repository includes a GitHub Actions workflow that automatically publishes to PyPI when you create a release.

### Setup

1. Create a PyPI API token:
   - Go to https://pypi.org/manage/account/token/
   - Create a new token with upload permissions
   - Copy the token (it starts with `pypi-`)

2. Add the token to GitHub Secrets:
   - Go to your repository on GitHub
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token

### Creating a Release

1. Update the version in `pyproject.toml`

2. Commit and push the changes:
```bash
git add pyproject.toml
git commit -m "Bump version to 0.1.0"
git push
```

3. Create a git tag:
```bash
git tag v0.1.0
git push origin v0.1.0
```

4. Create a release on GitHub:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Select the tag you created
   - Add release notes
   - Click "Publish release"

The GitHub Action will automatically build and publish the package to PyPI.

## Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

Examples:
- `0.1.0` - Initial release
- `0.1.1` - Bug fix
- `0.2.0` - New features
- `1.0.0` - First stable release

## Troubleshooting

### Authentication Issues

If you have trouble authenticating, use API tokens instead of passwords:
```bash
python -m twine upload --repository pypi dist/* --username __token__ --password pypi-YOUR-TOKEN
```

### File Already Exists Error

You cannot upload the same version twice. Increment the version number in `pyproject.toml` and rebuild.

### Import Errors After Installation

Make sure the package structure is correct:
```
src/
  wrtkit/
    __init__.py
    ...
```

And that `pyproject.toml` has:
```toml
[tool.setuptools.packages.find]
where = ["src"]
```
