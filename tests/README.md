# Test Suite

This directory contains the test suite for the jira2py library.

## Structure

- `unit/` - Unit tests with mocked external dependencies
- `integration/` - Integration tests that require a real Jira instance

## Running Tests

### Unit Tests (Recommended for development)

```bash
# Run all unit tests
make unit-test

# Or directly with pytest
uv run pytest tests/unit/
```

### Integration Tests (Require Jira credentials)

```bash
# Run all integration tests
make integration-test

# Or directly with pytest
uv run pytest tests/integration/ -m integration
```

### All Tests

```bash
# Run all tests
make test

# Or directly with pytest
uv run pytest
```

## Configuration

Integration tests require Jira credentials to be set in a `.env` file. 
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your Jira credentials
```

Never commit your `.env` file to version control.