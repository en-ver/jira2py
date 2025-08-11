# Scripts

This directory contains utility scripts for development and maintenance of the jira2py library.

## Available Scripts

### `fetch_test_data.py`

Fetches real data from a Jira instance and anonymizes it for use as test fixtures.

**Usage:**

```bash
python scripts/fetch_test_data.py
```

**Requirements:**

- JIRA_URL, JIRA_USER, and JIRA_API_TOKEN environment variables set
- Or .env file with these variables

**Output:**

- Creates anonymized JSON fixtures in `tests/fixtures/`
