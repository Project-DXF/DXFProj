.PHONY: help install install-dev test test-cov lint format type-check clean build docs run

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install the package"
	@echo "  install-dev  - Install with development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  type-check   - Run type checking"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build the package"
	@echo "  docs         - Build documentation"
	@echo "  run          - Run the application"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest

test-cov:
	pytest --cov=src/dxf_analyzer --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 src/ tests/

format:
	black src/ tests/

type-check:
	mypy src/

# Maintenance
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	python -m build

# Documentation
docs:
	@echo "Building documentation..."
	@echo "Documentation build not yet configured"

# Run application
run:
	python main.py 