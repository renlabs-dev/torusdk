# Torus SDK Development Guide

## Overview

The Torus SDK (`torusdk`) is a Python CLI tool for interacting with the Torus network. This project uses modern Python tooling with Nix for reproducible development environments.

## Quick Start

```sh
# Clone and enter directory
cd /path/to/torusdk

# Option 1: Using UV directly (recommended)
uv venv                        # Create virtual environment
uv sync                        # Install dependencies
just ci                        # Run linting and type checking

# Option 2: Using Nix development shell
nix develop                    # Enter development shell with UV/just
just install                   # Install dependencies (alias for uv sync)
just ci                        # Run linting and type checking

# View all available commands
just --list
```

## Development Environment

### Prerequisites

- **UV**: Modern Python dependency management
- **Just**: Task runner for development commands
- **Nix** (optional): Provides reproducible development environment

### Setup Options

#### Option 1: UV + Just (Recommended)

```sh
# Install UV and Just (see installation guides)
curl -LsSf https://astral.sh/uv/install.sh | sh   # Install UV
# Install just via package manager or cargo install just

uv venv                        # Create virtual environment
uv sync                        # Install dependencies including dev group
```

#### Option 2: Nix Development Shell

```sh
nix develop                    # Enter development shell with UV/just
just install                   # Install Python dependencies (alias for uv sync)
```

## Development Workflow

### Code Quality

```sh
# Format and fix linting issues
just fmt

# Check formatting and linting (CI mode)
just lint

# Run type checker only
just typecheck

# Run full CI checks
just ci
```

### Testing

Tests are now enabled and managed through pytest:

```sh
just test                      # Run tests (quiet mode)
just cov                       # Run tests with coverage reporting
just cov-html                  # Generate HTML coverage report
```

Test configuration is defined in `pyproject.toml` under `[tool.pytest.ini_options]`.

### Documentation

```sh
just docs-run                  # Start local documentation server
just docs-build               # Generate documentation files
```

## Release Management

This project uses [Towncrier](https://towncrier.readthedocs.io/) for changelog management.

### Creating News Fragments

Check [changes/README.md](./changes/README.md) for details.

```sh
# Add a feature fragment
just news feature "Add new CLI command for balance checking" 123

# Add a bugfix fragment (orphan - no issue number)
just news bugfix "Fix edge case in key validation"

# Edit fragment in $EDITOR
just news-edit security 456

# Available types: feature, bugfix, doc, removal, misc, security
```

### Release Process

```sh
# Preview changelog without writing files
just changelog-preview

# Create a release (bumps version, generates changelog, creates git tag)
just release 0.3.0

# Build and publish to PyPI (requires PYPI_API_TOKEN in environment)
just build
just publish
```

## Project Structure

```text
torusdk/
├── src/torusdk/           # Main package source
│   ├── cli/              # CLI command implementations
│   ├── compat/           # Compatibility utilities
│   ├── faucet/           # Faucet functionality
│   ├── types/            # Type definitions
│   └── util/             # Utility modules
├── nix/                  # Nix configuration files
├── changes/              # Towncrier news fragments
├── tests/                # Test files (currently empty)
├── pyproject.toml        # Python project configuration
├── poetry.lock           # Dependency lockfile
├── flake.nix            # Nix flake configuration
└── justfile             # Task runner recipes
```

## Configuration Files

### `pyproject.toml`

- **Project metadata**: Name, version, dependencies (UV-compatible format)
- **Build system**: Hatchling for modern Python packaging
- **Ruff**: Linting and formatting settings
- **BasedPyright**: Type checking configuration
- **Pytest**: Test configuration and coverage settings
- **Towncrier**: Changelog generation settings
- **UV**: Default dependency groups configuration

### Tool Configurations

- **Line length**: 80 characters (Ruff)
- **Python version**: 3.10+ target
- **Type checking**: Strict mode with BasedPyright
- **Import sorting**: Handled by Ruff

## CI/CD

The project uses GitHub Actions with Ubicloud runners and UV for fast dependency management:

- **Workflow**: `.github/workflows/check-code.yml`
- **Matrix testing**: Python 3.10, 3.12
- **Setup**: astral-sh/setup-uv with caching enabled
- **Checks**: Linting, type checking, testing, coverage, build validation
- **PR Requirements**: Towncrier fragment must be added

### CI Commands

All CI operations use the same commands as local development:

```sh
just lint                      # Linting and formatting checks
just typecheck                 # Type checking
just test                      # Run tests
just cov                       # Generate coverage report
just build                     # Package building
just news-check                # Enforce changelog fragments on PRs
```

## Nix Integration

### Development Shell

```sh
nix develop                    # Enter development shell
nix develop --command just ci  # Run CI in Nix shell
```

### Flake Commands

```sh
just nix-check                 # Check Nix flake validity
just nix-update                # Update flake inputs
```

## Common Tasks

### Adding a New CLI Command

1. Create the command module in `src/torusdk/cli/`
2. Register it in `src/torusdk/cli/__init__.py`
3. Add tests in `tests/cli/` (when tests are enabled)
4. Create news fragment: `just news feature "Add new command"`
5. Update documentation if needed

### Updating Dependencies

```sh
uv lock --upgrade              # Update to latest compatible versions
uv sync                        # Sync updated dependencies to environment
```

### Debugging

The development environment includes IPython for interactive debugging:

```python
# In your code
import IPython; IPython.embed()
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you have activated UV environment (`uv sync`) or are in Nix development shell
2. **Type checking failures**: Check that all imports have proper type stubs
3. **Formatting issues**: Run `just fmt` to auto-fix most formatting problems
4. **UV sync failures**: Try `uv lock --upgrade` to refresh dependencies
5. **Nix build failures**: Try `nix flake update` or check the Nix configuration

### Getting Help

- Use `just help <command>` to see detailed information about specific commands
- Check the [justfile](./justfile) for all available recipes
- Review CI logs for detailed error information
- Consult the [Towncrier documentation](https://towncrier.readthedocs.io/) for changelog management
