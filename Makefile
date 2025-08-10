.PHONY: help lint type-check all-checks

help:
	@echo "Available targets:"
	@echo "  lint          - Run Python linting with ruff"
	@echo "  type-check    - Run Python type checking with mypy"
	@echo "  all-checks    - Run all checks"

lint:
	uv run ruff check src/

type-check:
	uv run mypy src/

all-checks: lint type-check
	@echo "All checks passed!"