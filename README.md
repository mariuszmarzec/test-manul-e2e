# WebFrame

A lightweight Python library for web application development, providing core data processing, filtering, transformation, and utility functions.

## Features

- **DataProcessor**: Process and transform datasets with mapping, aggregation, and pagination
- **Filter**: Flexible filtering with equality, range, contains, and custom conditions
- **Transformer**: Transform data structures with pluggable rules
- **Utilities**: Input validation, sanitization, response formatting, and more

## Installation

```bash
pip install -e .
```

Or install for development:

```bash
pip install -e ".[test]"
```

## Quick Start

### DataProcessor

```python
from mylib.core import DataProcessor

data = [
    {"id": 1, "name": "Alice", "score": 85},
    {"id": 2, "name": "Bob", "score": 92},
    {"id": 3, "name": "Charlie", "score": 78},
]

processor = DataProcessor(data)

# Aggregate scores
total = processor.aggregate("score", "sum")
average = processor.aggregate("score", "avg")

# Map values
processor.map("score", lambda s: s * 10)

# Paginate
result = processor.paginate(page=1, per_page=2)
```

### Filter

```python
from mylib.core import Filter

data = [
    {"name": "Alice", "age": 30, "role": "admin"},
    {"name": "Bob", "age": 25, "role": "user"},
    {"name": "Charlie", "age": 35, "role": "user"},
]

# Filter by equality
admins = Filter(data).where("role", "admin").apply()

# Filter by range
senior_users = Filter(data).where_gt("age", 30).apply()

# Chain conditions
filtered = Filter(data).where("role", "user").where_gt("age", 25).apply()
```

### Transformer

```python
from mylib.core import Transformer

data = [{"name": "alice", "age": 30, "email": "alice@example.com"}]

# Rename and add computed fields
transformer = (
    Transformer()
    .rename("name", "full_name")
    .compute_field("is_adult", lambda x: x["age"] >= 18)
    .remove_field("email")
)

result = transformer.apply(data)
```

### Utilities

```python
from mylib.utils import (
    validate_input,
    sanitize_string,
    format_response,
    parse_query_string,
    deep_merge,
)

# Validate input
result = validate_input(
    {"name": "test", "value": 123},
    required_fields=["name", "value"],
    types={"value": int}
)

# Sanitize input
clean_text = sanitize_string("<script>alert('xss')</script>Hello")

# Format API response
response = format_response(data={"items": [1, 2, 3]}, meta={"page": 1})

# Parse query string
params = parse_query_string("page=1&limit=10")

# Deep merge dictionaries
merged = deep_merge({"a": {"b": 1}}, {"a": {"c": 2}})
```

## API Reference

### DataProcessor Methods

| Method | Description |
|--------|-------------|
| `process(func)` | Apply function to each item |
| `map(key, func)` | Apply function to specific field |
| `aggregate(key, operation)` | Aggregate values (sum, avg, min, max, count) |
| `first()` | Get first item |
| `last()` | Get last item |
| `limit(n)` | Return first n items |
| `paginate(page, per_page)` | Return paginated results |
| `to_dict()` | Convert to dictionary |

### Filter Methods

| Method | Description |
|--------|-------------|
| `where(key, value)` | Equality filter |
| `where_not(key, value)` | Inequality filter |
| `where_gt(key, value)` | Greater than |
| `where_lt(key, value)` | Less than |
| `where_gte(key, value)` | Greater than or equal |
| `where_lte(key, value)` | Less than or equal |
| `where_contains(key, value)` | Contains filter |
| `where_in(key, values)` | In list filter |
| `apply()` | Apply all conditions |

### Transformer Methods

| Method | Description |
|--------|-------------|
| `rename(old, new)` | Rename a field |
| `add_field(name, value)` | Add constant field |
| `compute_field(name, func)` | Add computed field |
| `remove_field(name)` | Remove a field |
| `apply(data)` | Apply to list of items |
| `apply_single(item)` | Apply to single item |

### Utility Functions

| Function | Description |
|----------|-------------|
| `validate_input(data, required, types)` | Validate input data |
| `sanitize_string(value, max_length)` | Sanitize string input |
| `format_response(data, status, message, meta)` | Format API response |
| `parse_query_string(query)` | Parse URL query string |
| `generate_id()` | Generate UUID |
| `deep_merge(base, override)` | Deep merge dictionaries |
| `flatten_dict(d)` | Flatten nested dict |
| `chunk_list(lst, size)` | Split list into chunks |
| `safe_get(d, key_path, default)` | Safely get nested value |
| `truncate_text(text, max_length)` | Truncate text |
| `to_snake_case(text)` | Convert to snake_case |
| `to_camel_case(text)` | Convert to camelCase |

## Running Tests

```bash
pytest tests/test_core.py -v
```

With coverage:

```bash
pytest tests/test_core.py -v --cov=mylib --cov-report=term-missing
```

## Project Structure

```
.
├── mylib/
│   ├── __init__.py      # Package initialization
│   ├── core.py          # DataProcessor, Filter, Transformer
│   └── utils.py         # Utility functions
├── tests/
│   ├── __init__.py
│   └── test_core.py     # Comprehensive test suite
├── calculator.py        # Simple calculator utility with add function
├── setup.py             # Package configuration
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## License

MIT License


## Manul E2E suites

The Manul checks live in isolated directories and do not modify the WebFrame
library or its existing tests.

### Standalone extraction and installer safety

The `standalone-manul-e2e/` suite clones the Manul source at
`MANUL_E2E_REF` (defaults to `main`) and exercises the real
installer, repair helper, and environment bootstrap using a disposable
`HOME`, temporary runtime directory, and fake host commands.

It verifies:

- canonical scripts and runtime symlinks resolve to the standalone checkout;
- the installer preserves a pre-existing SQLite database and refuses to
  fabricate state when no database exists;
- repair refuses to create a new database when no valid backup exists;
- unattended environment bootstrap preserves operator settings, refreshes
  canonical/host-skill paths atomically, and uses mode 0600;
- operator-specific configuration and credential values are not committed or
  printed by the harness.

Run locally:

```bash
python -m pip install pytest
pytest -q standalone-manul-e2e/test_extraction.py
```

The GitHub Actions workflow runs this suite on relevant pull requests and
pushes. To validate a different Manul branch or commit:

```bash
MANUL_E2E_REF=<branch-or-commit> pytest -q standalone-manul-e2e/test_extraction.py
```

The suite does not start the daemon or connect to GitHub, Todo Desktop, Fiteo,
or Caracal. It does not access the operator's real `~/.manul` or credentials.


### Mandatory gate before full live E2E on the operator machine

The green GitHub Actions job above is an isolated installer-safety test. It is
**not** the full live Manul E2E run.

Do not start the live scenarios from issue #28 until all three related PRs have
been merged:

1. `mariuszmarzec/manul#1` — standalone runtime becomes available on `main`.
2. `mariuszmarzec/globalskills#128` — host integration points to standalone
   Manul on `main`.
3. `mariuszmarzec/test-manul-e2e#29` — the extraction E2E harness is merged.

Then the operator machine must be updated and bootstrapped before any live E2E:

1. Pull the merged `main` changes for `globalskills`, `manul`, and
   `test-manul-e2e` (use fast-forward-only updates; do not test stale local
   checkouts).
2. Check Manul's daemon/task state, then intentionally stop the old runtime.
   Keep a rollback archive of the old `~/.manul` and `~/.manul-repo` until
   the fresh installation is verified. The fresh runtime itself must be
   initialized from the standalone repository, not from the legacy
   `globalskills/skills/manul-github-bot` source.
3. Clone/update standalone Manul at `~/.manul-repo`, set
   `MANUL_CANONICAL_DIR=~/.manul-repo/skills/manul-github-bot` and
   `MANUL_HOST_SKILLS_DIR=~/.globalskills/skills`, then perform a deliberate
   fresh install with `install-manul.sh --init-state` against the new runtime.
   Restore only operator-owned configuration and credentials from the approved
   local secret/config sources; never copy them into Git.
4. Verify that runtime entrypoints resolve into `~/.manul-repo`, the runtime
   DB is the new one, `.env` has mode `0600`, the daemon is not accidentally
   started by installation, and `manul status`/intentional start behave as
   expected.
5. Only after the operator confirms this clean installation is healthy, run
   the full live E2E scenarios. Record the exact repository SHAs and the fresh
   runtime verification results with the test run.

This gate is host/manual work and is deliberately not simulated by ordinary
Linux CI. Never run a cleanup or fresh-install step against a live daemon or a
runtime containing active tasks. The operator may discard the old runtime data
after the fresh installation is accepted; keep the rollback archive until then.
