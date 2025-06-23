# Contributing to Scale API Compose Pilot

Thank you for your interest in contributing to Scale API Compose Pilot! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- TrueNAS Scale (Electric Eel or later) for testing
- Git

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/scale-api-compose-pilot.git
   cd scale-api-compose-pilot
   ```

3. Install the TrueNAS API client:
   ```bash
   pip install git+https://github.com/truenas/api_client.git
   ```

4. Install the project in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Before Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Ensure all tests pass:
   ```bash
   pytest
   ```

3. Run code quality checks:
   ```bash
   ruff check .
   black --check .
   mypy scale_api_compose_pilot/
   ```

### Making Changes

1. Write your code following the project's style guidelines
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests and linters pass

### Code Style Guidelines

- **Python Style**: Follow PEP 8 via Black formatter
- **Type Hints**: Add type hints to all public functions and methods
- **Documentation**: Use clear docstrings for all public APIs
- **Imports**: Use isort for import ordering
- **Line Length**: 88 characters maximum

### Testing

- Write unit tests for new functions and classes
- Test both success and error cases
- Use pytest fixtures for common test setup
- Mock external dependencies (TrueNAS API calls)

Example test structure:
```python
def test_deploy_compose_stack():
    """Test Docker Compose deployment."""
    # Test implementation
    pass

def test_deploy_compose_stack_invalid_file():
    """Test deployment with invalid compose file."""
    # Test error handling
    pass
```

### Documentation

- Update README.md for new features
- Add docstrings to all public functions
- Include examples in docstrings where helpful
- Update API documentation

## Submitting Changes

### Pull Request Process

1. Ensure your branch is up to date with main:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. Run the full test suite:
   ```bash
   pytest
   ruff check .
   black --check .
   mypy scale_api_compose_pilot/
   ```

3. Commit your changes with a clear message:
   ```bash
   git commit -m "feat: add support for multi-service compose files"
   ```

4. Push to your fork and create a pull request

### Commit Message Guidelines

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

Examples:
```
feat: add shell autocompletion support
fix: handle connection timeouts gracefully
docs: update API examples in README
test: add tests for discovery module
```

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: Explain what changes you made and why
- **Testing**: Describe how you tested your changes
- **Breaking Changes**: Note any breaking changes
- **Issues**: Reference any related issues

PR Template:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass
- [ ] Manual testing completed
- [ ] Added new tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
```

## Code Quality

### Automated Checks

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **Pytest**: Testing
- **Pre-commit**: Git hooks for quality checks

### Security

- Use `bandit` for security scanning
- Never commit secrets or API keys
- Use environment variables for sensitive data
- Validate all user inputs

## Project Structure

```
scale_api_compose_pilot/
├── __init__.py          # Package initialization
├── cli.py              # Command-line interface
├── manager.py          # Core TrueNAS management
├── discovery.py        # Network discovery
├── exceptions.py       # Custom exceptions
├── setup_wizard.py     # Interactive setup
└── ai_helper.py        # AI assistance features

tests/
├── __init__.py
├── test_manager.py     # Manager tests
└── test_cli.py         # CLI tests

examples/
├── nginx-webserver.yml # Example compose files
└── postgres-database.yml
```

## Feature Requests

### Community Priorities

Based on community feedback, these features are most requested:

1. **Multi-service compose support** - Deploy complex stacks
2. **Network configuration** - Custom networks and macvlan
3. **Migration tools** - From Docker/Portainer to TrueNAS
4. **Volume management** - IX volumes and bind mounts
5. **Template system** - Pre-built app templates

### Proposing New Features

1. Check existing issues for similar requests
2. Create a detailed feature request issue
3. Discuss the approach with maintainers
4. Create a proposal document for large features

## Bug Reports

### Before Reporting

1. Check if the issue exists in the latest version
2. Search existing issues
3. Try to reproduce with minimal steps

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the problem

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. See error

**Expected behavior**
What you expected to happen

**Environment:**
- OS: [e.g. macOS 12.0]
- Python version: [e.g. 3.11]
- Package version: [e.g. 0.1.0]
- TrueNAS version: [e.g. 24.10]

**Additional context**
Any other context about the problem
```

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backwards compatible)
- Patch: Bug fixes

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create release PR
5. Tag release
6. GitHub Actions publishes to PyPI

## Community

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community chat
- **Documentation**: Check README and docstrings

### Communication Guidelines

- Be respectful and inclusive
- Search before asking questions
- Provide context and examples
- Help others when you can

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

Thank you for contributing to Scale API Compose Pilot! 🚀