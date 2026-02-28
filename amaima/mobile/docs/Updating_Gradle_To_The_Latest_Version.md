# AMAIMA Android — Gradle Upgrade Guide
## From Gradle 8.14.2 + Kotlin 1.9.20 → Gradle 9.3.1 + AGP 9.0.1 + KGP 2.3.10

**Do not attempt this in one step.** Each phase has a verification gate. Only
proceed to the next phase when the current one produces a clean `./gradlew build`.

---

## Pre-flight: Check JDK version

Gradle 9.x requires JDK 17+ for the daemon. Verify before starting:

```bash
java -version          # must show 17+ or 21+
./gradlew --version    # shows current Gradle + JVM version
```

If on JDK 11 or lower, install JDK 17 from [Adoptium](https://adoptium.net/)
and update `JAVA_HOME` or set it in Android Studio:
**File → Project Structure → SDK Location → JDK location**

---

## Phase 1 — Kotlin 1.9.20 → 2.1.21 (K2 compiler introduction)

**Why this first:** K2 is a breaking change for annotation processors. Testing K2
compatibility before touching AGP or KSP makes it easier to isolate issues.

### Files to change

**`gradle/libs.versions.toml`**:
```toml
kotlin = "2.1.21"   # was: "1.9.20"
ksp    = "2.1.21-1.0.29"  # KSP version prefix MUST match KGP
```

**`app/build.gradle.kts`** — update the compiler options block:
```kotlin
kotlin {
    jvmToolchain(17)
    compilerOptions {
        freeCompilerArgs.addAll("-opt-in=...")
    }
}
```
Remove any `kotlinOptions {}` block (deprecated in KGP 2.x).

### Verification
```bash
./gradlew help --warning-mode=all 2>&1 | grep -i "deprecat\|error\|warn"
./gradlew assembleDebug
./gradlew test
```

**Expected issues and fixes:**

| Symptom | Fix |
|---------|-----|
| `kotlinOptions is deprecated` | Replace with `compilerOptions {}` block |
| `freeCompilerArgs = listOf(...)` | Change to `freeCompilerArgs.addAll(...)` |
| Hilt annotation processing error | Expected — fixed in Phase 2 (KSP migration) |
| `sourceCompatibility = 18` at project level | Move inside `java {}` or `kotlin {}` block |

---

## Phase 2 — kapt → KSP (Hilt + Room)

**Why this second:** KSP is required for Hilt compatibility with Kotlin 2.x and
AGP 9.x. This is the riskiest change for AMAIMA because Hilt generates all the
DI graph code via the annotation processor.

### Files to change

**`gradle/libs.versions.toml`**:
```toml
ksp  = "2.1.21-1.0.29"  # KSP, already set in Phase 1
hilt = "2.52"           # 2.52+ has stable KSP support
room = "2.7.1"          # 2.7.x has stable KSP support
```

**`app/build.gradle.kts`** — plugin block:
```kotlin
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.ksp)          // ADD
    alias(libs.plugins.hilt)
    // kotlin("kapt")                // REMOVE
}
```

**`app/build.gradle.kts`** — dependency block:
```kotlin
// Hilt
ksp(libs.hilt.android.compiler)         // was: kapt(libs.hilt.android.compiler)

// Room
ksp(libs.room.compiler)                 // was: kapt(libs.room.compiler)
```

**Remove the `kapt {}` configuration block** if present:
```kotlin
// DELETE this entire block if it exists:
kapt {
    correctErrorTypes = true
}
```

**Add the `ksp {}` configuration block** instead:
```kotlin
ksp {
    arg("room.schemaLocation", "${layout.projectDirectory}/schemas")
    arg("room.incremental", "true")
    arg("dagger.hilt.android.internal.disableAndroidSuperclassValidation", "true")
}
```

### Verification
```bash
./gradlew assembleDebug
```

**Expected issues and fixes:**

| Symptom | Fix |
|---------|-----|
| `@HiltAndroidApp not found` | Ensure `ksp` plugin applied BEFORE `hilt` plugin |
| Room `@Database` entity missing | Add `ksp { arg("room.schemaLocation", ...) }` |
| `Cannot access 'kapt' as it is removed` | All `kapt()` deps switched to `ksp()` |
| KSP error: `Hilt does not support...` | Verify hilt version is 2.52+ |

**Files to manually verify in AMAIMA after this phase:**
- `di/` directory — all `@Module`, `@InstallIn`, `@Provides` annotations
- `OnDeviceMLManager.kt` — check if Hilt-injected, verify `@Inject` works
- All Room `@Dao` and `@Entity` files — verify KSP generates them correctly

---

## Phase 3 — AGP 8.x → 8.7.x (intermediate landing)

**Why this step exists:** Jumping from AGP 8.0.x directly to 9.0.1 skips several
deprecation warnings that become errors. Landing on 8.7 first surfaces those
warnings before they become failures.

### Files to change

**`gradle/libs.versions.toml`**:
```toml
agp = "8.7.3"   # intermediate — not 9.0.1 yet
```

**`gradle/wrapper/gradle-wrapper.properties`**:
```properties
# Keep 8.14.2 at this phase — 8.7.x AGP works with Gradle 8.x
distributionUrl=https\://services.gradle.org/distributions/gradle-8.14.2-bin.zip
```

### Verification
```bash
./gradlew help --warning-mode=all
./gradlew assembleDebug
./gradlew assembleRelease
```

Fix all warnings before Phase 5 — they become errors under AGP 9.x.

**Common warnings at this phase:**

| Warning | Fix before Phase 5 |
|---------|--------------------|
| `Variant API usage` — `applicationVariants` | Migrate to `androidComponents { onVariants {} }` |
| `BaseExtension` type usage | Use new public interfaces |
| Density splits in use | Use App Bundles instead |
| `dexOptions` block present | Remove — dex is automatic in AGP 8+ |

---

## Phase 4 — Target SDK 34 → 36

**Why before Phase 5:** AGP 9.0.1 sets `targetSdk = compileSdk` by default.
Getting to SDK 36 now, while still on Gradle 8.x, means fewer moving parts.

### ONNX Runtime 1.20.0 SDK 36 compatibility
ONNX Runtime 1.20.0 supports Android API 36. No API changes to `OnDeviceMLManager.kt`.
The NNAPI delegate check should already guard API level:
```kotlin
// Verify this pattern exists in OnDeviceMLManager.kt:
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) { // API 28
    sessionOptions.addNnapi()
}
```

### TFLite 2.18.0 SDK 36 compatibility
TFLite 2.18.0 supports API 36. GPU delegate is only beneficial on API 31+.
`VisionEngine.kt` and `AudioEngine.kt` should handle gracefully on API 26.

### Files to change

**`gradle/libs.versions.toml`**:
```toml
compileSdk = "36"
targetSdk  = "36"
# onnxRuntime = "1.20.0"   # upgrade now too
# tensorflowLite = "2.18.0"  # upgrade now too
```

### Verification
```bash
./gradlew assembleDebug
# Run on a physical API 36 device or emulator
# Run on a physical API 26 device — verify ONNX/TFLite fallbacks work
```

---

## Phase 5 — Gradle 9.3.1 + AGP 9.0.1 + KGP 2.3.10 (FINAL)

All the provided files in this package represent this final state.

### Apply all the provided files

```bash
# 1. Replace your gradle/libs.versions.toml with the provided one
# 2. Replace your project-level build.gradle.kts
# 3. Replace your app/build.gradle.kts
# 4. Replace your settings.gradle.kts
# 5. Replace your gradle.properties
# 6. Replace your gradle/wrapper/gradle-wrapper.properties

# 7. Update the wrapper JAR to match:
./gradlew wrapper --gradle-version=9.3.1

# 8. Run AGP Upgrade Assistant in Android Studio:
#    Tools → AGP Upgrade Assistant → select 9.0.1
```

### First build sequence

```bash
# Step 1: Check for deprecation warnings (don't fix build failures yet)
./gradlew help --warning-mode=all 2>&1 | tee upgrade-warnings.txt

# Step 2: Full clean build
./gradlew clean assembleDebug 2>&1 | tee upgrade-build.txt

# Step 3: Tests
./gradlew test

# Step 4: Release build (verifies R8 full mode + proguard rules)
./gradlew assembleRelease
```

### AGP 9.x specific issues to watch for

**1. Built-in Kotlin enabled by default**

AGP 9.x has runtime dependency on KGP 2.2.10+ and enables built-in Kotlin mode.
You may see this warning:
```
The 'kotlin-android' plugin is redundant when built-in Kotlin is enabled.
```
This is safe to ignore. Or remove `alias(libs.plugins.kotlin.android)` from
app `build.gradle.kts` if you want to rely fully on AGP's built-in mode.

**2. Legacy variant API removed**

If any Gradle plugin you use accesses `applicationVariants` or `variantFilter`,
it will fail at configuration time. Check third-party plugins for AGP 9 support.

**3. R8 full mode**

`android.enableR8.fullMode=true` in gradle.properties enables aggressive shrinking.
Verify these AMAIMA-specific keep rules exist in `proguard-rules.pro`:

```proguard
# ONNX Runtime — keep native model loading
-keep class ai.onnxruntime.** { *; }
-dontwarn ai.onnxruntime.**

# TFLite — keep interpreter and ops
-keep class org.tensorflow.lite.** { *; }
-dontwarn org.tensorflow.lite.**

# Hilt — keep DI graph (usually auto-generated, but just in case)
-keep class dagger.hilt.** { *; }
-keep class hilt_aggregated_deps.** { *; }

# Room — keep entity classes
-keep @androidx.room.Entity class * { *; }
-keepclassmembers @androidx.room.Entity class * { *; }

# Retrofit — keep API interfaces
-keep interface com.amaima.app.network.** { *; }
-keepattributes Signature
-keepattributes Exceptions
```

**4. Libraries minimum compile SDK**

AGP 9.x enforces that library `minCompileSdk` matches or is below your app's
`compileSdk`. If you see:
```
Library X has minCompileSdk 35 but compileSdk is 34
```
Update `compileSdk = "36"` in `libs.versions.toml` (already done in Phase 4).

---

## Version Compatibility Matrix

| Component | Current | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 (Final) |
|-----------|---------|---------|---------|---------|---------|-----------------|
| Gradle | 8.14.2 | 8.14.2 | 8.14.2 | 8.14.2 | 8.14.2 | **9.3.1** |
| AGP | unknown | same | same | **8.7.3** | 8.7.3 | **9.0.1** |
| KGP | 1.9.20 | **2.1.21** | 2.1.21 | 2.1.21 | 2.1.21 | **2.3.10** |
| KSP | kapt | kapt | **2.1.21-1.0.29** | same | same | **2.3.10-1.0.31** |
| Hilt | unknown | same | **2.52** | same | same | 2.52 |
| Room | unknown | same | **2.7.1** | same | same | 2.7.1 |
| ONNX RT | 1.16.3 | same | same | same | **1.20.0** | 1.20.0 |
| TFLite | 2.14.0 | same | same | same | **2.18.0** | 2.18.0 |
| Min SDK | 26 | 26 | 26 | 26 | 26 | 26 |
| Target SDK | 34 | 34 | 34 | 34 | **36** | 36 |
| JDK | any | **17+** | 17+ | 17+ | 17+ | 17+ |

---

## If Things Go Wrong

**Quick rollback:** The only file that's hard to un-do is the wrapper jar update.
Keep a copy of your original `gradle/wrapper/gradle-wrapper.jar` before running
`./gradlew wrapper --gradle-version=9.3.1`.

**Build scan:** If a phase fails and you can't diagnose from the log:
```bash
./gradlew assembleDebug --scan
```
Paste the scan URL — it shows the full task graph, configuration cache hits/misses,
and dependency resolution tree.

**Hilt KSP not finding components:** Ensure clean build after KSP migration:
```bash
./gradlew clean
rm -rf app/build/
./gradlew assembleDebug
```

**K2 compiler incompatibility:** If a library doesn't support K2 yet, you can
temporarily downgrade the language version while keeping KGP 2.x:
```kotlin
compilerOptions {
    languageVersion.set(KotlinVersion.KOTLIN_1_9)  // temporary escape hatch
}
```
