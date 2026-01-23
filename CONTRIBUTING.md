# Contributing to NovaIR

Thank you for your interest in contributing to NovaIR!

## Project Status

NovaIR is a **research prototype** released as a community gift. Contributions are welcome but not guaranteed to be merged.

## How to Contribute

### Reporting Issues

- Search existing issues before creating a new one
- Provide a minimal reproducible example when possible
- Include NovaIR version and environment details

### Pull Requests

1. **Fork** the repository
2. **Create a branch** for your changes
3. **Write tests** if applicable
4. **Follow the code style** of the project
5. **Submit a PR** with a clear description

### What We're Looking For

Contributions that are especially welcome:

- **Documentation improvements** — Clarifications, examples, typo fixes
- **Bug fixes** — With tests demonstrating the fix
- **Examples** — Real-world use cases in `.novair` format
- **Test coverage** — Additional edge cases

### What We're NOT Looking For

- Major architectural changes without prior discussion
- Features that increase complexity without clear benefit
- Changes that break existing tests

## Code Style

- Python: Follow PEP 8
- NovaIR: Follow the examples in `examples/`
- Documentation: Clear, concise, English

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Questions?

Open an issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

*Thank you for helping improve NovaIR!*
