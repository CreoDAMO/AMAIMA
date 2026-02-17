# Updated GitHub Actions Workflow: `.github/workflows/backend.yml`

Copy the YAML below and paste it into your `.github/workflows/backend.yml` file on GitHub.

## What Changed and Why

1. **Removed redundant `pip install pytest`** - pytest and pytest-asyncio are now in `requirements.txt`, so they get installed automatically.
2. **Removed `pytest --collect-only || exit 0` guard** - This was masking real failures by exiting with success if collection failed.
3. **Added `-v --tb=short` flags** - Better test output for diagnosing failures in CI logs.

## Updated Workflow

```yaml
name: Backend CI/CD
permissions:
  contents: read

on:
  push:
    branches: [ main ]
    paths: [ 'amaima/backend/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'amaima/backend/**' ]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - name: Install dependencies
        run: |
          cd amaima/backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install httpx
      - name: Run tests
        run: |
          cd amaima/backend
          pytest -v --tb=short
```

## Other Files That Were Updated

These files were already updated in the Replit codebase and will be pushed with the next sync:

- **`amaima/backend/requirements.txt`** - Added `pytest` and `pytest-asyncio` to the testing section.
- **`amaima/backend/pytest.ini`** - Created with `asyncio_mode = auto` and `pythonpath = .` so pytest can find the `app` module.
- **`amaima/backend/conftest.py`** - Ensures the backend directory is on the Python path.

These three files are what actually fix the 38 test failures. The workflow YAML update is just cleanup.
