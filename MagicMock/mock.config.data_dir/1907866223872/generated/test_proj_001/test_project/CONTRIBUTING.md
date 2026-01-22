# Contributing to Test Project

Thank you for your interest in contributing to Test Project! We welcome contributions from everyone.

## How to Contribute

### Reporting Bugs
- Check existing issues to avoid duplicates
- Provide a clear description and steps to reproduce
- Include your environment details (OS, Python version, etc.)

### Suggesting Enhancements
- Explain the enhancement and use case
- Provide examples of how it would work
- Explain why this enhancement would be useful

### Submitting Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests as needed
5. Ensure all tests pass (`make test`)
6. Ensure code is formatted (`make format`)
7. Commit with clear messages
8. Push to your fork
9. Submit a pull request with a clear description

## Development Setup

```bash
git clone https://github.com/yourusername/Test Project.git
cd Test Project
make install-dev
```

## Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with:
- Line length: 100 characters
- Use type hints
- Document all public functions

We use these tools:
- **black** for formatting
- **ruff** for linting
- **mypy** for type checking

Run `make format` and `make lint` before submitting.

## Testing

All new features must include tests:

```bash
make test
```

Aim for >80% code coverage.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## Questions?

Feel free to open an issue for any questions.
