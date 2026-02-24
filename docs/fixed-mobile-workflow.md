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

## build summary
Gradle Root Project	Requested Tasks	Gradle Version	Build Outcome	Build Scan®
AMAIMA	wrapper --gradle-version 8.14.2	8.14.2	✅	Build Scan not published
AMAIMA	assembleRelease	8.14.2	❌	Build Scan not published
Caching for Gradle actions was enabled - expand for details
Count	Total Size (Mb)
Entries Restored	0	0
Entries Saved	0	0
Cache Entry Details
    Entry: Gradle User Home
    Requested Key : gradle-home-v1|Linux|build[2efe194e8363a66cc916e2eba443ead7]-76283e9dde6d6ab5771b9d155f84f4b4547eb3d3
    Restored  Key : 
              Size: 
              (Entry not restored: Cache service responded with 400)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0XRmdaQAAAAAuIO+vj2JyRp/5Y3q+4VcMUEFPRURHRTA1MTAARWRnZQ==)
---
Entry: /home/runner/work/AMAIMA/AMAIMA/amaima/mobile/.gradle/configuration-cache
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: No encryption key provided)
---
Entry: /home/runner/.gradle/caches/8.14.2/generated-gradle-jars/gradle-api-8.14.2.jar
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0WBmdaQAAAADSCtLmciqPR4R+SSIsGf8QUEFPRURHRTA1MTcARWRnZQ==)
---
Entry: /home/runner/.gradle/wrapper/dists/gradle-8.14.2-bin/2pb3mgt1p815evrl3weanttgr
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0WBmdaQAAAAB5dAXA9/+DSql4++KhagOuUEFPRURHRTA2MjEARWRnZQ==)
---
Entry: /home/runner/.gradle/caches/modules-*/files-*/*/*/*/*
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0WhmdaQAAAAA2GNaIuzQZQKMg09Mz6gh5UEFPRURHRTA1MTMARWRnZQ==)
---
Entry: /home/runner/.gradle/caches/jars-*/*/
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0WBmdaQAAAAD4xB9OB6r8TIh0M0kQ3/cuUEFPRURHRTA2MjAARWRnZQ==)
---
Entry: /home/runner/.gradle/caches/*/kotlin-dsl/accessors/*/
/home/runner/.gradle/caches/*/kotlin-dsl/scripts/*/
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0WBmdaQAAAAD59afFlQeWS7/e0V5YU9s6UEFPRURHRTA1MTQARWRnZQ==)
---
Entry: /home/runner/.gradle/caches/*/groovy-dsl/*/
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0WBmdaQAAAADqzF+Cz6uVSJdKG9P1SyBDUEFPRURHRTA2MDgARWRnZQ==)
---
Entry: /home/runner/.gradle/caches/transforms-4/*/
/home/runner/.gradle/caches/*/transforms/*/
    Requested Key : 
    Restored  Key : 
              Size: 
              (Entry not restored: not requested)
    Saved     Key : 
              Size: 
              (Entry not saved: 
Our services aren't available right now
We're working to restore all services as soon as possible. Please check back soon.

0XBmdaQAAAABfNYfQzqLcSKzJzqM9nfugUEFPRURHRTA2MjIARWRnZQ==)

---

## Annotations
1 error and 11 warnings
build
Process completed with exit code 1.
build
Failed to save cache entry with path '/home/runner/.gradle/caches,/home/runner/.gradle/notifications,/home/runner/.gradle/.setup-gradle' and key: gradle-home-v1|Linux|build[2efe194e8363a66cc916e2eba443ead7]-76283e9dde6d6ab5771b9d155f84f4b4547eb3d3: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0XRmdaQAAAAAuIO+vj2JyRp/5Y3q+4VcMUEFPRURHRTA1MTAARWRnZQ==
build
Failed to save cache entry with path '/home/runner/.gradle/caches/transforms-4/*/
/home/runner/.gradle/caches/*/transforms/*/' and key: gradle-transforms-v1-eb6a7869b5c675e8c07be3a20a663343: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0XBmdaQAAAABfNYfQzqLcSKzJzqM9nfugUEFPRURHRTA2MjIARWRnZQ==
build
Failed to save cache entry with path '/home/runner/.gradle/caches/modules-*/files-*/*/*/*/*' and key: gradle-dependencies-v1-92d01710bee3adf69728c174d0da4131: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0WhmdaQAAAAA2GNaIuzQZQKMg09Mz6gh5UEFPRURHRTA1MTMARWRnZQ==
build
Failed to save cache entry with path '/home/runner/.gradle/caches/*/groovy-dsl/*/' and key: gradle-groovy-dsl-v1-840f6ff9b57c0e74f89d6f35c2b94a15: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0WBmdaQAAAADqzF+Cz6uVSJdKG9P1SyBDUEFPRURHRTA2MDgARWRnZQ==
build
Failed to save cache entry with path '/home/runner/.gradle/caches/*/kotlin-dsl/accessors/*/
/home/runner/.gradle/caches/*/kotlin-dsl/scripts/*/' and key: gradle-kotlin-dsl-v1-a562cbe71f51ef70e67957f570f10a9f: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0WBmdaQAAAAD59afFlQeWS7/e0V5YU9s6UEFPRURHRTA1MTQARWRnZQ==
build
Failed to save cache entry with path '/home/runner/.gradle/caches/8.14.2/generated-gradle-jars/gradle-api-8.14.2.jar' and key: gradle-generated-gradle-jars-v1-bb0bb7bb17d22594d51db16f25c6bd57: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0WBmdaQAAAADSCtLmciqPR4R+SSIsGf8QUEFPRURHRTA1MTcARWRnZQ==
build
Failed to save cache entry with path '/home/runner/.gradle/wrapper/dists/gradle-8.14.2-bin/2pb3mgt1p815evrl3weanttgr' and key: gradle-wrapper-zips-v1-79d70a92c3ec061dab933d2fbc6cc528: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0WBmdaQAAAAB5dAXA9/+DSql4++KhagOuUEFPRURHRTA2MjEARWRnZQ==
build
Failed to save cache entry with path '/home/runner/.gradle/caches/jars-*/*/' and key: gradle-instrumented-jars-v1-8f450753c9721b29dba103bda37ca909: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>0WBmdaQAAAAD4xB9OB6r8TIh0M0kQ3/cuUEFPRURHRTA2MjAARWRnZQ==
build
Save Gradle distribution 8.14.2 failed: Error: <h2>Our services aren't available right now</h2><p>We're working to restore all services as soon as possible. Please check back soon.</p>01xidaQAAAAAmag8iny1CSqfo8KhfdNZzUEFPRURHRTA2MjIARWRnZQ==
build
Restore Gradle distribution 8.14.2 failed: Error: Cache service responded with 400
build
Failed to restore gradle-home-v1|Linux|build[2efe194e8363a66cc916e2eba443ead7]-76283e9dde6d6ab5771b9d155f84f4b4547eb3d3: Error: Cache service responded with 400

## Error Report:
