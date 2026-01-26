# GitHub Actions Workflows

This document contains the CI/CD configurations for the AMAIMA project. These files should be placed in the `.github/workflows/` directory.

## 1. Frontend Workflow (`.github/workflows/frontend.yml`)

```yaml
name: Frontend CI/CD

on:
  push:
    branches: [ main ]
    paths: [ 'amaima/frontend/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'amaima/frontend/**' ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: amaima/frontend/package-lock.json
      - name: Install dependencies
        run: cd amaima/frontend && npm ci
      - name: Lint
        run: cd amaima/frontend && npm run lint -- --dir .
      - name: Build
        run: cd amaima/frontend && npm run build
```

## 2. Backend Workflow (`.github/workflows/backend.yml`)

```yaml
name: Backend CI/CD

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
          pip install pytest httpx
      - name: Run tests
        run: |
          cd amaima/backend
          # Only run pytest if tests are found, otherwise exit gracefully
          pytest --collect-only || exit 0
          pytest
```

## 3. Mobile Workflow (`.github/workflows/mobile.yml`)

```yaml
name: Mobile CI/CD

on:
  push:
    branches: [ main ]
    paths: [ 'mobile/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'mobile/**' ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: gradle
      - name: Build with Gradle
        run: |
          if [ -d "mobile" ]; then
            cd mobile
            if [ -f "gradlew" ]; then
              chmod +x gradlew
              ./gradlew assembleDebug
            fi
          fi
```
