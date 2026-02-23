# Mobile CI/CD Workflow

```yml
name: Mobile CI/CD

permissions:
  contents: read

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
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
          distribution: temurin
          java-version: '17'

      - name: Cache Gradle files
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('amaima/mobile/**/*.gradle*', 'amaima/mobile/**/gradle-wrapper.properties') }}
          restore-keys: |
            gradle-${{ runner.os }}-

      - name: Grant execute permission for Gradle wrapper
        run: chmod +x gradlew

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
          path: "**/build/outputs/**/*.apk"
```

# Add files via upload #25

## Error:
```txt
Run ./gradlew assembleRelease --no-daemon
  ./gradlew assembleRelease --no-daemon
  shell: /usr/bin/bash -e {0}
  env:
    JAVA_HOME: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
    JAVA_HOME_17_X64: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
    KEYSTORE_PASSWORD: ***
    KEY_ALIAS: ***
    KEY_PASSWORD: ***
Error: Invalid or corrupt jarfile /home/runner/work/AMAIMA/AMAIMA/amaima/mobile/gradle/wrapper/gradle-wrapper.jar
Error: Process completed with exit code 1.
```

# Delete amaima/mobile/gradle/wrapper/gradle-wrapper.jar #26

## Error:
```txt
Run ./gradlew assembleRelease --no-daemon
  ./gradlew assembleRelease --no-daemon
  shell: /usr/bin/bash -e {0}
  env:
    JAVA_HOME: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
    JAVA_HOME_17_X64: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
    KEYSTORE_PASSWORD: ***
    KEY_ALIAS: ***
    KEY_PASSWORD: ***
Error: Unable to access jarfile /home/runner/work/AMAIMA/AMAIMA/amaima/mobile/gradle/wrapper/gradle-wrapper.jar
Error: Process completed with exit code 1.
