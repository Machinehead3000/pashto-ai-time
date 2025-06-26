.PHONY: help install test lint format check-format check-types check-deps clean

# Project information
PROJECT_NAME := pashto-ai
PYTHON := python
PIP := pip

# Directories
SRC_DIR := aichat
TESTS_DIR := tests

help:
	@echo "\n\033[1m$(PROJECT_NAME) - Development Tools\033[0m"
	@echo "========================================"
	@echo "\nAvailable commands:\n"
	@echo "\033[1mDevelopment:\033[0m"
	@echo "  make install        Install development dependencies"
	@echo "  make dev            Run the application in development mode"
	@echo "  make test           Run all tests"
	@echo "  test-coverage       Run tests with coverage report"
	@echo "\nCode Quality:\033[0m"
	@echo "  make lint           Run all linters"
	@echo "  make format         Format code with black and isort"
	@echo "  make check-format   Check code formatting"
	@echo "  make check-types    Run type checking"
	@echo "  make check-deps     Check for outdated dependencies"
	@echo "\nBuild & Deploy:\033[0m"
	@echo "  make build          Build the package"
	@echo "  make clean          Remove build artifacts"

# Development
install:
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt
	pre-commit install

dev:
	$(PYTHON) -m aichat

test:
	$(PYTHON) -m pytest -v $(TESTS_DIR)/

test-coverage:
	$(PYTHON) -m pytest --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html $(TESTS_DIR)/

# Code Quality
lint:
	ruff check $(SRC_DIR) $(TESTS_DIR)
	black --check $(SRC_DIR) $(TESTS_DIR)
	mypy $(SRC_DIR) $(TESTS_DIR)

format:
	black $(SRC_DIR) $(TESTS_DIR)
	ruff check --fix $(SRC_DIR) $(TESTS_DIR)

check-format:
	black --check $(SRC_DIR) $(TESTS_DIR)

check-types:
	mypy $(SRC_DIR) $(TESTS_DIR)

check-deps:
	$(PIP) list --outdated

# Build & Deploy
build:
	$(PYTHON) -m build

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf dist/ build/ htmlcov/ .coverage .mypy_cache/ .pytest_cache/ .ruff_cache/
