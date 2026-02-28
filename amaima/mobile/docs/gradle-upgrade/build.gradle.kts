// ============================================================================
// AMAIMA Android — Project-level build.gradle.kts
// ============================================================================
// UPGRADE PATH SUMMARY (from current state):
//   Phase 1: Kotlin 1.9.20  → 2.1.21  (safe K2 intermediate, test first)
//   Phase 2: kapt           → KSP      (required before AGP 9.x)
//   Phase 3: AGP            → 8.7.x    (intermediate landing point)
//   Phase 4: Target SDK 34  → 36       (verify ONNX/TFLite compat first)
//   Phase 5: Gradle 9.3.1 + AGP 9.0.1 + KGP 2.3.10  ← THIS FILE
//
// JDK REQUIREMENT: JDK 17+ required for Gradle 9.x daemon.
//   Set in Android Studio: File → Project Structure → SDK Location → JDK
//   Or export JAVA_HOME=/path/to/jdk17
// ============================================================================

plugins {
    // AGP 9.0.1 requires Gradle 9.1.0 minimum (we use 9.3.1)
    // AGP 9.x enables built-in Kotlin by default — see app/build.gradle.kts
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false

    // KGP 2.3.10 is the first version with full Gradle 9.0 support (no deprecations)
    // Minimum KGP for Gradle 9.0.0 is 2.0.0, but 2.3.10 recommended
    alias(libs.plugins.kotlin.android) apply false

    // KSP replaces kapt for annotation processing (Hilt, Room)
    // kapt is deprecated in Kotlin 2.x + AGP 9.x
    alias(libs.plugins.ksp) apply false

    // Hilt Gradle plugin (project-level — applies annotation processor config)
    alias(libs.plugins.hilt) apply false
}

// Project-wide configuration
// Note: In Gradle 9.x, direct property assignments like `buildDir = ...`
// are removed. Use layout.buildDirectory in subproject build files instead.
