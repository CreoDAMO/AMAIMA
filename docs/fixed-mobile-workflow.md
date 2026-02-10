# Fixed Mobile CI/CD Workflow

The original `.github/workflows/mobile.yml` fails at the "Cache Gradle files" step with:

```
Error: Key Validation Error: gradle-$( {{ runner.os }}- ){{ hashFiles('mobile/**/*.gradle*', 'mobile/**/gradle-wrapper.properties') }} cannot contain commas.
```

**Root Cause:** The `key` field in the cache step has malformed template expressions — `\(` and `\)` instead of proper `${{ }}` syntax. This causes the `hashFiles()` call (which contains a comma-separated argument list) to not be evaluated as an expression, leaving literal commas in the cache key string.

**Fix:** Replace the broken `key` line with proper GitHub Actions expression syntax.

---

## Fixed `mobile.yml`

Copy the content below and replace your `.github/workflows/mobile.yml` file:

```yaml
name: Mobile CI/CD

permissions:
  contents: read
  actions: read

on:
  push:
    branches: [ main ]
    paths:
      - 'mobile/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'mobile/**'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: mobile

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Cache Gradle files
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('mobile/**/*.gradle*', 'mobile/**/gradle-wrapper.properties') }}
          restore-keys: |
            gradle-${{ runner.os }}-

      - name: Grant execute permission for Gradle wrapper
        run: chmod +x gradlew

      - name: Build Debug APK
        run: ./gradlew assembleDebug --no-daemon

      - name: Verify APK output
        run: |
          APK_COUNT=$(find . -type f -name "*.apk" | wc -l)
          if [ "$APK_COUNT" -eq 0 ]; then
            echo "APK not generated"
            exit 1
          fi
          echo "APK(s) generated: $APK_COUNT"

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: amaima-debug-apk
          path: mobile/**/build/outputs/**/*.apk
```

## What Changed

**Line 36 (the `key` field):**

| Before (broken) | After (fixed) |
|---|---|
| `key: gradle-\( {{ runner.os }}- \){{ hashFiles('mobile/**/*.gradle*', 'mobile/**/gradle-wrapper.properties') }}` | `key: gradle-${{ runner.os }}-${{ hashFiles('mobile/**/*.gradle*', 'mobile/**/gradle-wrapper.properties') }}` |

The fix uses proper `${{ }}` expression syntax so that `hashFiles()` is correctly evaluated as a GitHub Actions expression instead of being treated as a literal string containing commas.
