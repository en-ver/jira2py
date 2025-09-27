.PHONY: lint format type-check check clean help

help:
	@echo "Available targets:"
	@echo "  lint        - Run ruff linting with auto-fix"
	@echo "  format      - Run ruff formatting"
	@echo "  type-check  - Run mypy type checking"
	@echo "  check       - Run all checks (lint, format, type-check)"
	@echo "  clean       - Clean Python cache files"
	@echo "  help        - Show this help message"

# Run ruff linting with auto-fix
lint:
	ruff check --fix src examples

# Run ruff formatting
format:
	ruff format src examples

# Run mypy type checking
type-check:
	mypy src/jira2py/ --show-error-codes --strict

# Run all checks
check: lint format type-check

# Clean Python cache files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .mypy_cache/ .ruff_cache/
