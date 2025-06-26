# Contributing to NEO-AI CHAT

Thank you for your interest in contributing to NEO-AI CHAT! We welcome all contributions, whether they're bug reports, feature requests, documentation improvements, or code contributions.

## 📋 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 🐛 Reporting Bugs

1. **Check Existing Issues**: Before creating a new issue, please check if the bug has already been reported.
2. **Create an Issue**: If you're the first to report the bug, create a new issue with a clear title and description.
3. **Provide Details**: Include steps to reproduce the bug, expected behavior, actual behavior, and any relevant screenshots or error messages.

## 💡 Feature Requests

We welcome feature requests! Please create an issue with:
- A clear description of the feature
- The problem it solves
- Any alternative solutions you've considered
- Additional context or screenshots

## 🛠 Development Setup

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/neo-ai-chat.git
   cd neo-ai-chat
   ```
3. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install development dependencies**
   ```bash
   pip install -e .[dev]
   ```
5. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

## 📝 Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use type hints for all function signatures
- Keep lines under 100 characters
- Document all public functions and classes with docstrings
- Write tests for new functionality

## 🧪 Testing

Run tests with:
```bash
pytest
```

## 📦 Building the Package

To create a distributable package:
```bash
python setup.py sdist bdist_wheel
```

## 🚀 Submitting a Pull Request

1. Fork the repository and create your feature branch
2. Commit your changes with a clear commit message
3. Push to your fork and submit a pull request

## 📜 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
