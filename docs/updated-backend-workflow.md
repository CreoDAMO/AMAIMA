# Updated GitHub Actions Workflow: `.github/workflows/backend.yml`

Copy the YAML below and paste it into your `.github/workflows/backend.yml` file on GitHub.

## What Changed and Why

1. **Added environment variables** - The app imports modules that reference `DATABASE_URL`, `API_SECRET_KEY`, and `NVIDIA_NIM_API_KEY` at startup. Without these set (even to dummy values), middleware and billing code can fail during test collection when `main.py` is imported.
2. **Added `PYTHONPATH`** - Ensures pytest can resolve `app.*` imports from the backend directory without relying solely on `pytest.ini`.
3. **Removed redundant `pip install pytest httpx`** - Both are already in `requirements.txt`.
4. **Removed `pytest --collect-only || exit 0` guard** - This was masking real failures by exiting with success if collection failed.
5. **Added `cache-dependency-path`** - Points pip cache to the actual requirements file for faster CI runs.
6. **Added `-v --tb=short` flags** - Better test output for diagnosing failures in CI logs.

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
    env:
      DATABASE_URL: ""
      API_SECRET_KEY: "test_secret_key_for_ci"
      NVIDIA_NIM_API_KEY: "test_nim_key_for_ci"
      PYTHONPATH: "."
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: amaima/backend/requirements.txt
      - name: Install dependencies
        run: |
          cd amaima/backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd amaima/backend
          pytest tests/ -v --tb=short
```

## Supporting Files

These files in the codebase support the CI pipeline:

- **`amaima/backend/requirements.txt`** - Includes `pytest`, `pytest-asyncio`, and `httpx` in the dependencies.
- **`amaima/backend/pytest.ini`** - Configured with `asyncio_mode = auto`, `pythonpath = .`, and `testpaths = tests`.
- **`amaima/backend/conftest.py`** - Adds the backend directory to `sys.path` for module resolution.

## Notes

- **63 total tests**: 55 unit tests (routing, agents, crews, workflows) + 8 integration tests (full app endpoints, caching, rate limiting).
- All tests use mocks for external services (NVIDIA NIM API, database calls) so no live services are needed in CI.
- The environment variables (`DATABASE_URL`, `API_SECRET_KEY`, `NVIDIA_NIM_API_KEY`) are set to dummy values so the app can import cleanly without connecting to real services.
- `PYTHONPATH: "."` ensures pytest resolves `app.*` imports from the backend directory.
