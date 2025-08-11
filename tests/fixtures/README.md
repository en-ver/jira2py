# Test Fixtures

This directory contains anonymized sample data that matches the structure of real Jira API responses for use in tests.

## Files

- `fields.json` - Sample issue fields data
- `search_results.json` - Sample issue search results
- `issue_details.json` - Sample detailed issue data
- `changelogs.json` - Sample issue changelog data
- `comments.json` - Sample issue comments data

## Usage

These fixtures are used in unit tests to provide realistic data structures without requiring a real Jira connection.

## Generation

Fixtures can be regenerated using the `scripts/fetch_test_data.py` script, which connects to a real Jira instance, fetches sample data, and anonymizes it for safe storage.