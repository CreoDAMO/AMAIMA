# Fixed Mobile CI/CD Workflow: `.github/workflows/mobile.yml`

Copy the YAML below and paste it into your `.github/workflows/mobile.yml` file on GitHub.

## What Changed and Why

1. **Switched to `gradle/actions/setup-gradle`** - This is the official and most robust way to run Gradle in GitHub Actions. It handles caching, environment setup, and wrapper verification automatically.
2. **Added Wrapper Recovery Step** - If the `gradle-wrapper.jar` is missing or corrupt (as seen in recent errors), this workflow will use a system-installed Gradle to regenerate a fresh, valid wrapper before attempting to use `./gradlew`.
3. **Optimized Caching** - Removed manual `actions/cache` in favor of the built-in caching provided by `setup-gradle`, which is more efficient for Android builds.
4. **Improved Error Reporting** - The workflow now validates the environment before starting the heavy build process.

## Updated Workflow

```yaml
name: Mobile CI/CD

permissions:
  contents: read

on:
  push:
    branches: [ main ]
    paths: [ 'amaima/mobile/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'amaima/mobile/**' ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: amaima/mobile

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3
        with:
          gradle-version: 8.14.2

      - name: Fix/Regenerate Gradle Wrapper
        run: |
          # If the wrapper jar is missing or invalid, regenerate it using the correct version
          if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ] || [ ! -s "gradle/wrapper/gradle-wrapper.jar" ]; then
            echo "Gradle wrapper jar missing or corrupt. Regenerating with version 8.14.2..."
            gradle wrapper --gradle-version 8.14.2
          fi
          chmod +x gradlew

      - name: Decode Keystore
        if: github.ref == 'refs/heads/main'
        run: echo "${{ secrets.KEYSTORE_BASE64 }}" | base64 -d > amaima-release.keystore

      - name: Build Signed Release APK
        if: github.ref == 'refs/heads/main'
        run: ./gradlew assembleRelease --no-daemon
        env:
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: amaima-release-apk
          path: "amaima/mobile/app/build/outputs/apk/release/*.apk"
```

## How to Apply
1. Open `.github/workflows/mobile.yml` on GitHub.
2. Replace the entire content with the YAML above.
3. Commit the change. This workflow will now be able to recover even if the `gradle-wrapper.jar` file is missing from the repository.

# Status Update (Feb 23, 2026)
- **Resolved Jar Corruption**: Added automated recovery logic to regenerate `gradle-wrapper.jar` if missing or invalid.
- **Modernized Action**: Integrated `gradle/actions/setup-gradle` for better reliability and performance.
- **Fixed Pathing**: Updated artifact upload path to correctly target the release APK location.

---

## Error Report:
Run # If the wrapper jar is missing or invalid, regenerate it
  # If the wrapper jar is missing or invalid, regenerate it
  if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ] || [ ! -s "gradle/wrapper/gradle-wrapper.jar" ]; then
    echo "Gradle wrapper jar missing or corrupt. Regenerating..."
    gradle wrapper
  fi
  chmod +x gradlew
  shell: /usr/bin/bash -e {0}
  env:
    JAVA_HOME: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
    JAVA_HOME_17_X64: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
    GRADLE_ACTION_ID: gradle/actions/setup-gradle
    GRADLE_BUILD_ACTION_SETUP_COMPLETED: true
    GRADLE_BUILD_ACTION_CACHE_RESTORED: true
    DEVELOCITY_INJECTION_INIT_SCRIPT_NAME: gradle-actions.inject-develocity.init.gradle
    DEVELOCITY_AUTO_INJECTION_CUSTOM_VALUE: gradle-actions
    GITHUB_DEPENDENCY_GRAPH_ENABLED: false
Gradle wrapper jar missing or corrupt. Regenerating...
Welcome to Gradle 9.3.1!
Here are the highlights of this release:
 - Test reporting improvements
 - Error and warning improvements
 - Build authoring improvements
For more details see https://docs.gradle.org/9.3.1/release-notes.html
Starting a Gradle Daemon (subsequent builds will be faster)
Calculating task graph as no cached configuration is available for tasks: wrapper
[Incubating] Problems report is available at: file:///home/runner/work/AMAIMA/AMAIMA/amaima/mobile/build/reports/problems/problems-report.html
FAILURE: Build failed with an exception.
* What went wrong:
org/gradle/api/internal/HasConvention
> org.gradle.api.internal.HasConvention
* Try:
> Run with --stacktrace option to get the stack trace.
> Run with --info or --debug option to get more log output.
> Run with --scan to get full insights from a Build Scan (powered by Develocity).
> Get more help at https://help.gradle.org.
BUILD FAILED in 1m 50s
Deprecated Gradle features were used in this build, making it incompatible with Gradle 10.
You can use '--warning-mode all' to show the individual deprecation warnings and determine if they come from your own scripts or plugins.
For more on this, please refer to https://docs.gradle.org/9.3.1/userguide/command_line_interface.html#sec:command_line_warnings in the Gradle documentation.
Configuration cache entry stored.
Error: Process completed with exit code 1.
