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
1m 1s
Run ./gradlew assembleRelease --no-daemon
Downloading https://services.gradle.org/distributions/gradle-8.14.2-bin.zip
.............10%.............20%.............30%.............40%.............50%.............60%.............70%.............80%.............90%..............100%
To honour the JVM settings for this build a single-use Daemon process will be forked. For more on this, please refer to https://docs.gradle.org/8.14.2/userguide/gradle_daemon.html#sec:disabling_the_daemon in the Gradle documentation.
Daemon will be stopped at the end of the build 
Calculating task graph as no cached configuration is available for tasks: assembleRelease
> Task :app:preBuild UP-TO-DATE
> Task :app:preReleaseBuild UP-TO-DATE
> Task :app:checkKotlinGradlePluginConfigurationErrors
> Task :app:extractProguardFiles
> Task :app:generateReleaseBuildConfig
> Task :app:buildKotlinToolingMetadata
> Task :app:generateReleaseResValues
> Task :app:createReleaseCompatibleScreenManifests
> Task :app:generateReleaseResources
> Task :app:javaPreCompileRelease
> Task :app:mapReleaseSourceSetPaths
> Task :app:extractDeepLinksRelease
> Task :app:checkReleaseAarMetadata
> Task :app:packageReleaseResources
> Task :app:mergeReleaseJniLibFolders

> Task :app:processReleaseMainManifest
[org.tensorflow:tensorflow-lite:2.14.0] /home/runner/.gradle/caches/8.14.2/transforms/2e17a794639dc98d8a4a0d27d44a48e9/transformed/tensorflow-lite-2.14.0/AndroidManifest.xml Warning:
	Namespace 'org.tensorflow.lite' is used in multiple modules and/or libraries: org.tensorflow:tensorflow-lite:2.14.0, org.tensorflow:tensorflow-lite-api:2.14.0. Please ensure that all modules and libraries have a unique namespace. For more information, See https://developer.android.com/studio/build/configure-app-module#set-namespace
[org.tensorflow:tensorflow-lite-support:0.4.4] /home/runner/.gradle/caches/8.14.2/transforms/e1c87f087bdd12e6dc0d124e7367d04d/transformed/tensorflow-lite-support-0.4.4/AndroidManifest.xml Warning:
	Namespace 'org.tensorflow.lite.support' is used in multiple modules and/or libraries: org.tensorflow:tensorflow-lite-support:0.4.4, org.tensorflow:tensorflow-lite-support-api:0.4.4. Please ensure that all modules and libraries have a unique namespace. For more information, See https://developer.android.com/studio/build/configure-app-module#set-namespace

> Task :app:processReleaseManifest
> Task :app:parseReleaseLocalResources
> Task :app:mergeReleaseResources
> Task :app:mergeReleaseNativeLibs
> Task :app:processReleaseManifestForPackage

> Task :app:stripReleaseDebugSymbols
Unable to strip the following libraries, packaging them as they are: libonnxruntime.so, libonnxruntime4j_jni.so, libonnxruntime_extensions4j_jni.so, libortextensions.so, libtensorflowlite_jni.so.

> Task :app:mergeReleaseArtProfile
> Task :app:mergeReleaseShaders FROM-CACHE
> Task :app:compileReleaseShaders NO-SOURCE
> Task :app:generateReleaseAssets UP-TO-DATE
> Task :app:extractReleaseNativeSymbolTables
> Task :app:mergeReleaseNativeDebugMetadata NO-SOURCE
> Task :app:processApplicationManifestReleaseForBundle
> Task :app:collectReleaseDependencies
> Task :app:sdkReleaseDependencyData
> Task :app:writeReleaseAppMetadata
> Task :app:writeReleaseSigningConfigVersions
> Task :app:mergeReleaseAssets FROM-CACHE
> Task :app:compressReleaseAssets
> Task :app:processReleaseResources
> Task :app:checkReleaseDuplicateClasses
> Task :app:bundleReleaseResources
e: [ksp] ModuleProcessingStep was unable to process 'com.amaima.app.di.RepositoryModule' because 'error.NonExistentClass' could not be resolved.

> Task :app:kspReleaseKotlin FAILED

Dependency trace:
    => element (CLASS): com.amaima.app.di.RepositoryModule
    => element (METHOD): bindAuthRepository(error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] ModuleProcessingStep was unable to process 'com.amaima.app.di.ServiceModule' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (CLASS): com.amaima.app.di.ServiceModule
    => element (METHOD): bindWebSocketManager(error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] ModuleProcessingStep was unable to process 'com.amaima.app.di.AppModule' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.AppModule
    => element (METHOD): provideNetworkMonitor(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] ModuleProcessingStep was unable to process 'com.amaima.app.di.NetworkModule' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.NetworkModule
    => element (METHOD): provideOkHttpClient(error.NonExistentClass,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] ModuleProcessingStep was unable to process 'com.amaima.app.di.DatabaseModule' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.DatabaseModule
    => element (METHOD): provideDatabase(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] ModuleProcessingStep was unable to process 'com.amaima.app.di.MLModule' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideContext(android.content.Context)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.AppModule
    => element (METHOD): provideNetworkMonitor(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideNetworkMonitor(android.content.Context)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.AppModule
    => element (METHOD): provideNetworkMonitor(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideEncryptedPreferences(android.content.Context)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.AppModule
    => element (METHOD): provideNetworkMonitor(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideOkHttpClient(error.NonExistentClass,error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.NetworkModule
    => element (METHOD): provideOkHttpClient(error.NonExistentClass,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideRetrofit(error.NonExistentClass,error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.NetworkModule
    => element (METHOD): provideOkHttpClient(error.NonExistentClass,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideAmaimaApi(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.NetworkModule
    => element (METHOD): provideOkHttpClient(error.NonExistentClass,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideWebSocketClient(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.NetworkModule
    => element (METHOD): provideOkHttpClient(error.NonExistentClass,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideMoshi()' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.NetworkModule
    => element (METHOD): provideOkHttpClient(error.NonExistentClass,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideDatabase(android.content.Context)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.DatabaseModule
    => element (METHOD): provideDatabase(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideQueryDao(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.DatabaseModule
    => element (METHOD): provideDatabase(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideWorkflowDao(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.DatabaseModule
    => element (METHOD): provideDatabase(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideUserDao(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.DatabaseModule
    => element (METHOD): provideDatabase(android.content.Context)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideModelDownloader(android.content.Context,error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideOnDeviceMLManager(android.content.Context,error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideModelRegistry(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideModelStore(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideEmbeddingEngine(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideAudioEngine(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideVisionEngine(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'provideVectorStore(android.content.Context)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (OBJECT): com.amaima.app.di.MLModule
    => element (METHOD): provideModelDownloader(android.content.Context,error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'bindAuthRepository(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (CLASS): com.amaima.app.di.RepositoryModule
    => element (METHOD): bindAuthRepository(error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'bindQueryRepository(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (CLASS): com.amaima.app.di.RepositoryModule
    => element (METHOD): bindAuthRepository(error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: [ksp] BindingMethodProcessingStep was unable to process 'bindWebSocketManager(error.NonExistentClass)' because 'error.NonExistentClass' could not be resolved.

Dependency trace:
    => element (CLASS): com.amaima.app.di.ServiceModule
    => element (METHOD): bindWebSocketManager(error.NonExistentClass)
    => type (ERROR return type): error.NonExistentClass

If type 'error.NonExistentClass' is a generated type, check above for compilation errors that may have prevented the type from being generated. Otherwise, ensure that type 'error.NonExistentClass' is on your classpath.
e: Error occurred in KSP, check log for detail


[Incubating] Problems report is available at: file:///home/runner/work/AMAIMA/AMAIMA/amaima/mobile/build/reports/problems/problems-report.html
FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':app:kspReleaseKotlin'.
> A failure occurred while executing org.jetbrains.kotlin.compilerRunner.GradleCompilerRunnerWithWorkers$GradleKotlinCompilerWorkAction
   > Compilation error. See log for more details

* Try:
> Run with --stacktrace option to get the stack trace.

> Run with --info or --debug option to get more log output.
> Run with --scan to get full insights.
Deprecated Gradle features were used in this build, making it incompatible with Gradle 9.0.
> Get more help at https://help.gradle.org.


You can use '--warning-mode all' to show the individual deprecation warnings and determine if they come from your own scripts or plugins.

For more on this, please refer to https://docs.gradle.org/8.14.2/userguide/command_line_interface.html#sec:command_line_warnings in the Gradle documentation.
BUILD FAILED in 1m
33 actionable tasks: 31 executed, 2 from cache
Configuration cache entry stored.
Error: Process completed with exit code 1.
