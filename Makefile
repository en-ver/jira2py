.PHONY: lint format type-check check clean help test test-cov test-verbose

help:
	@echo "Available targets:"
	@echo "  lint        - Run ruff linting with auto-fix"
	@echo "  format      - Run ruff formatting"
	@echo "  type-check  - Run mypy type checking"
	@echo "  test        - Run pytest test suite"
	@echo "  test-cov    - Run pytest with coverage report"
	@echo "  test-verbose- Run pytest with verbose output"
	@echo "  check       - Run all checks (lint, format, type-check, test)"
	@echo "  clean       - Clean Python cache files"
	@echo "  help        - Show this help message"

# Run ruff linting with auto-fix
lint:
	ruff check --fix src tests examples

# Run ruff formatting
format:
	ruff format src tests examples

# Run mypy type checking
type-check:
	mypy src/jira2py/ tests/ examples/ --show-error-codes --strict

# Run pytest test suite
test:
	pytest tests/ -v

# Run pytest with coverage report
test-cov:
	pytest tests/ --cov=src/jira2py --cov-report=html --cov-report=term

# Run pytest with verbose output
test-verbose:
	pytest tests/ -vv

# Run all checks
check: lint format type-check test

# Clean Python cache files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .mypy_cache/ .ruff_cache/ .pytest_cache/ htmlcov/ .coverage
