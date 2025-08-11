.PHONY: help format lint type-check test unit-test integration-test all-checks

help:
	@echo "Available targets:"
	@echo "  format           - Run Python formatter with ruff"
	@echo "  lint             - Run Python linting with ruff"
	@echo "  type-check       - Run Python type checking with mypy"
	@echo "  test             - Run all tests"
	@echo "  unit-test        - Run unit tests only"
	@echo "  integration-test - Run integration tests only"
	@echo "  all-checks       - Run all checks (format, lint, type-check, test)"

format:
	uv run ruff format

lint:
	uv run ruff check --fix

type-check:
	uv run mypy

test:
	uv run pytest

unit-test:
	uv run pytest tests/unit/

integration-test:
	uv run pytest tests/integration/ -m integration

all-checks: format lint type-check test
	@echo "All checks passed!"