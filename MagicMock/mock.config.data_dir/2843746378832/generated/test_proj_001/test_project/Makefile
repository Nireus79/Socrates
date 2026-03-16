.PHONY: help install install-dev test lint format clean build publish

help:
	@echo "Available commands:"
	@echo "  make install       - Install project in production mode"
	@echo "  make install-dev   - Install project with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Format code with black and ruff"
	@echo "  make type-check    - Run mypy type checking"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make build         - Build distribution packages"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

lint:
	ruff check .
	black --check .
	mypy . --ignore-missing-imports || true

format:
	black .
	ruff check . --fix

type-check:
	mypy . --ignore-missing-imports

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: clean
	python -m build

publish: build
	twine upload dist/*
