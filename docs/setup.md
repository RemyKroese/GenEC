# Setup and Installation

<div align="center">
  <img src="assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

## Context

GenEC setup involves installing Python dependencies and configuring the environment for execution or development workflows. The setup process uses `uv` as the modern Python package manager for fast, reliable dependency management with automatic virtual environment handling. This page assumes command execution from the root of the project.

### When to use
- **Execution**: Install base dependencies for running GenEC workflows
- **Development**: Install dev dependencies for code modification, testing, and quality checks
- **Distribution**: Install dist dependencies for building and packaging releases

## How to use

### Prerequisites

- Python 3.9 or higher
- Windows, Linux operating system
- Terminal / command line access

### Installation

**Step 1: Install uv package manager**
```bash
pip install uv
```

**Step 2: Choose your installation type**

| Installation Type | Command | Purpose |
|------------------|---------|---------|
| **Base (Users)** | `uv sync` | Run GenEC workflows |
| **Development** | `uv sync --group dev` | Contribute to GenEC |
| **Distribution** | `uv sync --group dist` | Build and package releases |

**Development dependencies include:**
- `pytest` - Testing framework with coverage reporting
- `mypy` - Type checking
- `flake8` / `pylint` - Code quality analysis
- `pre-commit` - Quality assurance hooks


## Verify installation
```bash
uv run python GenEC/main.py --version

uv run python GenEC/main.py basic --help
```

### Alternative: Portable Release

Download standalone executables from [GitHub Releases](https://github.com/RemyKroese/GenEC/releases):
```bash
# Windows
genec.exe --version
genec.exe --help

# Linux
./genec --version
./genec --help
```

## Development Testing Commands

Once you have the development environment set up, use these commands for code quality and testing:

**Testing Framework:**
```bash
# Run all tests
uv run pytest

# Run specific test types
uv run pytest -m unit                                     # Unit tests only
uv run pytest -m integration                              # Integration tests only
uv run pytest -m system                                   # System tests only

# Coverage reporting
uv run pytest --cov=. --cov-branch                        # Generate coverage report

# Repeat tests for stability
uv run pytest --count 10                                  # Run tests 10 times
```

**Code Quality Tools:**
```bash
# Type checking
uv run mypy .                                             # Type check entire project
uv run mypy GenEC/                                        # Type check production code only

# Code style and formatting
uv run flake8                                             # Code style checking

# Advanced code analysis
uv run pylint GenEC --score=yes                           # Production code linting (strict)
uv run pylint tests --rcfile=tests/.pylintrc --score=yes  # Test code linting (relaxed)
```

**Pre-commit Hooks:**
```bash
# Install and run pre-commit hooks
uv run pre-commit install                                 # Install hooks (one-time)
uv run pre-commit                                         # Run on staged files
uv run pre-commit run --all-files                         # Run on all files
```

## Environment Management

uv automatically creates and manages virtual environments:
```bash
# Virtual environment created automatically
uv sync

# Manual activation (if needed)
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows
```
## Next Steps

After successful setup:
- **New to GenEC?** → [Basic Workflow](workflows/basic.md)
- **Want automation?** → [Preset Workflow](workflows/preset.md)
- **Need batch processing?** → [Preset-list Workflow](workflows/preset-list.md)
