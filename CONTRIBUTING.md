# Contributing to Threads-Agent Stack

Thank you for your interest in contributing! This is a portfolio project, but I welcome feedback and suggestions.

## Ways to Contribute

1. **Report Issues**: Found a bug or have a suggestion? Open an issue!
2. **Documentation**: Help improve docs or add examples
3. **Code**: Submit PRs for bug fixes or improvements
4. **Ideas**: Share ideas for new features or architectural improvements

## Guidelines

### Code Style
- Python: Follow PEP 8, use type hints
- Use `ruff` for linting and `black` for formatting
- Write tests for new features (pytest)

### Commit Messages
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Examples:
  - `fix: correct API rate limiting in github_processor`
  - `feat: add CSV export to achievement collector`
  - `docs: update deployment guide for k8s 1.28`

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run `just check` to ensure all tests pass
5. Commit your changes
6. Push to your fork
7. Open a Pull Request with a clear description

## Development Setup

See the main README.md for setup instructions. Key commands:
- `just dev-start` - Start local development environment
- `just test` - Run all tests
- `just check` - Run linting, formatting, and tests

## Questions?

Feel free to reach out via [LinkedIn](https://www.linkedin.com/in/vitalii-serbyn-b517a083/) or open an issue for discussions!