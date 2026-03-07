.PHONY: lint format type-check check clean help test test-cov test-verbose build release docs docs-serve

help:
	@echo "Available targets:"
	@echo "  lint        - Run ruff linting with auto-fix"
	@echo "  format      - Run ruff formatting"
	@echo "  type-check  - Run ty type checking"
	@echo "  test        - Run pytest test suite"
	@echo "  test-cov    - Run pytest with coverage report"
	@echo "  test-verbose- Run pytest with verbose output"
	@echo "  check       - Run all checks (lint, format, type-check, test)"
	@echo "  build       - Build sdist and wheel"
	@echo "  release     - Create a release (usage: make release v=0.5.0)"
	@echo "  docs        - Build documentation"
	@echo "  docs-serve  - Serve documentation locally with live reload"
	@echo "  clean       - Clean Python cache files"
	@echo "  help        - Show this help message"

# Run ruff linting with auto-fix
lint:
	uv run ruff check --fix src tests examples

# Run ruff formatting
format:
	uv run ruff format src tests examples

# Run ty type checking
type-check:
	uv run ty check src/ tests/ examples/

# Run pytest test suite
test:
	uv run pytest tests/ -v

# Run pytest with coverage report
test-cov:
	uv run pytest tests/ --cov=src/jira2py --cov-report=html --cov-report=term

# Run pytest with verbose output
test-verbose:
	uv run pytest tests/ -vv

# Run all checks
check: lint format type-check test

# Build sdist and wheel
build: clean
	uv build

# Create a release: make release v=0.5.0
release:
ifndef v
	$(error Usage: make release v=0.5.0)
endif
	@echo "Releasing v$(v)..."
	@# Update version in pyproject.toml
	perl -i -pe 's/^version = ".*"/version = "$(v)"/' pyproject.toml
	@# Run all checks before releasing
	$(MAKE) check
	@# Commit, tag, and push
	git add pyproject.toml
	git diff --cached --quiet && echo "Version already set to $(v), skipping commit." || git commit -m "release: v$(v)"
	git tag -f "v$(v)"
	git push origin main "v$(v)" --force
	@echo "Release v$(v) pushed. CI will build, create GitHub Release, and publish to PyPI."

# Build documentation
docs:
	uv run --group docs mkdocs build

# Serve documentation locally with live reload
docs-serve:
	uv run --group docs mkdocs serve

# Clean Python cache files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .mypy_cache/ .ty/ .ruff_cache/ .pytest_cache/ htmlcov/ .coverage
