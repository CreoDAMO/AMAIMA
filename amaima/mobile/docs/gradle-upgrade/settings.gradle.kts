// ============================================================================
// AMAIMA Android — settings.gradle.kts
// ============================================================================
// GRADLE 9.x NOTE: settings.gradle.kts is now the canonical place to declare
// plugin and dependency repositories. Using allprojects { repositories {} }
// in the root build.gradle.kts is deprecated in 8.x and errors in 9.x.
// ============================================================================

pluginManagement {
    repositories {
        // Order matters — check Google first for Android plugins
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    // GRADLE 9.x: repositoriesMode enforces that all repos are declared here,
    // not in individual build.gradle.kts files. FAIL_ON_PROJECT_REPOS causes a
    // build error if any subproject tries to declare its own repositories.
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // ONNX Runtime is on Maven Central — no extra repo needed
        // TFLite is on Google Maven — covered by google() above
    }
}

rootProject.name = "amaima-mobile"
include(":app")
