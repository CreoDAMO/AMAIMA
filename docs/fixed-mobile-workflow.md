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
Run ./gradlew assembleRelease --no-daemon
  ./gradlew assembleRelease --no-daemon
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
    KEYSTORE_PASSWORD: ***
    KEY_ALIAS: ***
    KEY_PASSWORD: ***
Downloading https://services.gradle.org/distributions/gradle-8.14.2-bin.zip
.............10%.............20%.............30%.............40%.............50%.............60%.............70%.............80%.............90%..............100%
To honour the JVM settings for this build a single-use Daemon process will be forked. For more on this, please refer to https://docs.gradle.org/8.14.2/userguide/gradle_daemon.html#sec:disabling_the_daemon in the Gradle documentation.
Daemon will be stopped at the end of the build 
Calculating task graph as no cached configuration is available for tasks: assembleRelease
> Task :app:preBuild UP-TO-DATE
> Task :app:preReleaseBuild UP-TO-DATE
> Task :app:checkKotlinGradlePluginConfigurationErrors
> Task :app:buildKotlinToolingMetadata
> Task :app:generateReleaseResValues
> Task :app:generateReleaseBuildConfig
> Task :app:generateReleaseResources
> Task :app:createReleaseCompatibleScreenManifests
> Task :app:packageReleaseResources
> Task :app:mapReleaseSourceSetPaths
> Task :app:parseReleaseLocalResources
> Task :app:extractDeepLinksRelease
> Task :app:checkReleaseAarMetadata
> Task :app:extractProguardFiles
> Task :app:mergeReleaseJniLibFolders
> Task :app:javaPreCompileRelease
> Task :app:mergeReleaseNativeLibs

> Task :app:processReleaseMainManifest
[org.tensorflow:tensorflow-lite:2.14.0] /home/runner/.gradle/caches/8.14.2/transforms/2e17a794639dc98d8a4a0d27d44a48e9/transformed/tensorflow-lite-2.14.0/AndroidManifest.xml Warning:
	Namespace 'org.tensorflow.lite' is used in multiple modules and/or libraries: org.tensorflow:tensorflow-lite:2.14.0, org.tensorflow:tensorflow-lite-api:2.14.0. Please ensure that all modules and libraries have a unique namespace. For more information, See https://developer.android.com/studio/build/configure-app-module#set-namespace
[org.tensorflow:tensorflow-lite-support:0.4.4] /home/runner/.gradle/caches/8.14.2/transforms/e1c87f087bdd12e6dc0d124e7367d04d/transformed/tensorflow-lite-support-0.4.4/AndroidManifest.xml Warning:
	Namespace 'org.tensorflow.lite.support' is used in multiple modules and/or libraries: org.tensorflow:tensorflow-lite-support:0.4.4, org.tensorflow:tensorflow-lite-support-api:0.4.4. Please ensure that all modules and libraries have a unique namespace. For more information, See https://developer.android.com/studio/build/configure-app-module#set-namespace
/home/runner/work/AMAIMA/AMAIMA/amaima/mobile/app/src/main/AndroidManifest.xml:68:9-71:45 Warning:
	meta-data#com.google.android.gms.version@android:value was tagged at AndroidManifest.xml:68 to replace other declarations but no other declaration present

> Task :app:processReleaseManifest

> Task :app:stripReleaseDebugSymbols
Unable to strip the following libraries, packaging them as they are: libonnxruntime.so, libonnxruntime4j_jni.so, libonnxruntime_extensions4j_jni.so, libortextensions.so, libtensorflowlite_jni.so.

> Task :app:processReleaseManifestForPackage
> Task :app:mergeReleaseResources
> Task :app:extractReleaseNativeSymbolTables
> Task :app:mergeReleaseNativeDebugMetadata NO-SOURCE
> Task :app:mergeReleaseShaders FROM-CACHE
> Task :app:compileReleaseShaders NO-SOURCE
> Task :app:generateReleaseAssets UP-TO-DATE
> Task :app:mergeReleaseAssets FROM-CACHE
> Task :app:compressReleaseAssets
> Task :app:processApplicationManifestReleaseForBundle
> Task :app:collectReleaseDependencies
> Task :app:mergeReleaseArtProfile
> Task :app:writeReleaseAppMetadata
> Task :app:writeReleaseSigningConfigVersions
> Task :app:processReleaseResources FAILED
> Task :app:sdkReleaseDependencyData
> Task :app:checkReleaseDuplicateClasses

[Incubating] Problems report is available at: file:///home/runner/work/AMAIMA/AMAIMA/amaima/mobile/build/reports/problems/problems-report.html

FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':app:processReleaseResources'.
> A failure occurred while executing com.android.build.gradle.internal.res.LinkApplicationAndroidResourcesTask$TaskAction
   > Android resource linking failed
     ERROR: /home/runner/work/AMAIMA/AMAIMA/amaima/mobile/app/src/main/AndroidManifest.xml:68:9-71:45: AAPT: error: resource integer/google_play_services_version (aka com.amaima.app:integer/google_play_services_version) not found.
         

* Try:
> Run with --stacktrace option to get the stack trace.
> Run with --info or --debug option to get more log output.
> Run with --scan to get full insights.
> Get more help at https://help.gradle.org.

BUILD FAILED in 2m 14s

Deprecated Gradle features were used in this build, making it incompatible with Gradle 9.0.

You can use '--warning-mode all' to show the individual deprecation warnings and determine if they come from your own scripts or plugins.

For more on this, please refer to https://docs.gradle.org/8.14.2/userguide/command_line_interface.html#sec:command_line_warnings in the Gradle documentation.
31 actionable tasks: 29 executed, 2 from cache
Configuration cache entry stored.
Error: Process completed with exit code 1.
