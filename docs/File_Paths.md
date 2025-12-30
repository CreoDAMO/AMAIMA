# Current File Paths

## AMAIMA Paths
```plaintext
amaima
amaima/backend
amaima/backend/app
amaima/backend/app/core
amaima/backend/app/core/production_api_server.py
amaima/backend/app/core/progressive_model_loader.py
amaima/backend/app/core/unified_smart_router.py
amaima/backend/app/modules
amaima/backend/app/modules/multi_layer_verification_engine.py
amaima/backend/auth/token_validation.py
amaima/backend/middleware
amaima/backend/middleware/error_handler.py
amaima/backend/routers
amaima/backend/routers/query_router.py
amaima/backend/AMAIMA_Part_V_Comprehensive_Module_Integration_&_Final_Build_Specification.md
amaima/backend/PRESERVE_THESE.md
amaima/frontend
amaima/frontend/src
amaima/frontend/src/app
amaima/frontend/src/app/core
amaima/frontend/src/app/core/components
amaima/frontend/src/app/core/components/dashboard
amaima/frontend/src/app/core/components/dashboard/SystemMonitor.tsx
amaima/frontend/src/app/core/components/query
amaima/frontend/src/app/core/components/query/CodeBlock.tsx
amaima/frontend/src/app/core/components/query/QueryInput.tsx
amaima/frontend/src/app/core/components/query/QueryWithFile.tsx
amaima/frontend/src/app/core/components/query/StreamingResponse.tsx
amaima/frontend/src/app/core/components/ui
amaima/frontend/src/app/core/components/ui/badge.tsx
amaima/frontend/src/app/core/components/ui/button.tsx
amaima/frontend/src/app/core/components/ui/card.tsx
amaima/frontend/src/app/core/components/ui/textarea.tsx
amaima/frontend/src/app/core/hooks
amaima/frontend/src/app/core/hooks/useDebounce.ts
amaima/frontend/src/app/core/hooks/useMLInference.ts
amaima/frontend/src/app/core/hooks/useQuery.ts
amaima/frontend/src/app/core/lib
amaima/frontend/src/app/core/lib/api
amaima/frontend/src/app/core/lib/api/client.ts
amaima/frontend/src/app/core/lib/api/error-handler.ts
amaima/frontend/src/app/core/lib/api/queries.ts
amaima/frontend/src/app/core/lib/auth
amaima/frontend/src/app/core/lib/auth/auth-provider.tsx
amaima/frontend/src/app/core/lib/ml
amaima/frontend/src/app/core/lib/ml/complexity-estimator.ts
amaima/frontend/src/app/core/lib/stores
amaima/frontend/src/app/core/lib/stores/useAuthStore.ts
amaima/frontend/src/app/core/lib/stores/useQueryStore.ts
amaima/frontend/src/app/core/lib/stores/useSystemStore.ts
amaima/frontend/src/app/core/lib/sync
amaima/frontend/src/app/core/lib/sync/sync-manager.ts
amaima/frontend/src/app/core/lib/upload
amaima/frontend/src/app/core/lib/upload/file-uploader.ts
amaima/frontend/src/app/core/lib/utils
amaima/frontend/src/app/core/lib/utils/cn.ts
amaima/frontend/src/app/core/lib/utils/format.ts
amaima/frontend/src/app/core/lib/utils/secure-storage.ts
amaima/frontend/src/app/core/lib/utils/validation.ts
amaima/frontend/src/app/core/lib/websocket
amaima/frontend/src/app/core/lib/websocket/WebSocketProvider.tsx
amaima/frontend/src/app/core/lib/websocket/websocket-manager.ts
amaima/frontend/src/app/core/types
amaima/frontend/src/app/core/types/index.ts
amaima/frontend/src/app/globals.css
amaima/frontend/src/app/layout.tsx
amaima/frontend/src/app/page.tsx
amaima/frontend/src/middleware.ts
amaima/frontend/tests
amaima/frontend/tests/integration.spec.ts
amaima/frontend/AMAIMA_Frontend_Complete_Implementation_Guide.md
amaima/frontend/PRESERVE_THESE.md
amaima/mobile
amaima/mobile/app/src/main/java/com/amaima/app
amaima/mobile/app/src/main/java/com/amaima/app/androidTest
amaima/mobile/app/src/main/java/com/amaima/app/androidTest/IntegrationTest.kt
amaima/mobile/app/src/main/java/com/amaima/app/data
amaima/mobile/app/src/main/java/com/amaima/app/data/exception
amaima/mobile/app/src/main/java/com/amaima/app/data/exception/ApiException.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/local/entity
amaima/mobile/app/src/main/java/com/amaima/app/data/local/entity/QueryEntity.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/local/entity/QueryRepositoryImpl.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/remote
amaima/mobile/app/src/main/java/com/amaima/app/data/remote/api
amaima/mobile/app/src/main/java/com/amaima/app/data/remote/api/AmaimaApi.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/remote/interceptor
amaima/mobile/app/src/main/java/com/amaima/app/data/remote/interceptor/AuthInterceptor.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/remote/websocket
amaima/mobile/app/src/main/java/com/amaima/app/data/remote/websocket/AmaimaWebSocket.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/repository
amaima/mobile/app/src/main/java/com/amaima/app/data/repository/AuthRepository.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/sync
amaima/mobile/app/src/main/java/com/amaima/app/data/sync/SyncWorker.kt
amaima/mobile/app/src/main/java/com/amaima/app/data/websocket
amaima/mobile/app/src/main/java/com/amaima/app/data/websocket/WebSocketManager.kt
amaima/mobile/app/src/main/java/com/amaima/app/di
amaima/mobile/app/src/main/java/com/amaima/app/di/AppModule.kt
amaima/mobile/app/src/main/java/com/amaima/app/ml
amaima/mobile/app/src/main/java/com/amaima/app/ml/TensorFlowLiteManager.kt
amaima/mobile/app/src/main/java/com/amaima/app/presentation
amaima/mobile/app/src/main/java/com/amaima/app/presentation/AmaimaNavHost.kt
amaima/mobile/app/src/main/java/com/amaima/app/presentation/HomeScreen.kt
amaima/mobile/app/src/main/java/com/amaima/app/presentation/QueryScreen.kt
amaima/mobile/app/src/main/java/com/amaima/app/security
amaima/mobile/app/src/main/java/com/amaima/app/security/BiometricAuthManager.kt
amaima/mobile/app/src/main/java/com/amaima/app/security/EncryptedPreferences.kt
amaima/mobile/app/src/main/java/com/amaima/app/settings
amaima/mobile/app/src/main/java/com/amaima/app/settings/gradle.kt
amaima/mobile/app/src/main/java/com/amaima/app/ui/query
amaima/mobile/app/src/main/java/com/amaima/app/ui/query/QueryViewModel.kt
amaima/mobile/app/src/main/java/com/amaima/app/AmaimaApplication.kt
amaima/mobile/app/src/main/java/com/amaima/app/proguard-rules.pro
amaima/mobile/AMAIMA_Android_Client_Complete_APK_Design_Specification.md
amaima/tests
amaima/tests/conftest.py
docs
docs/charts
docs/charts/Charts.md
docs/development-deployment
docs/development-deployment/AMAIMA_Platform_Development_&_Deployment_Strategy.md
docs/executive-summary
docs/executive-summary/AMAIMA_System_Executive_Summary.md
docs/integration
docs/integration/AMAIMA_System_Integration_Guide.md
docs/summary
docs/summary/Backend_Frontend_Mobie_Integration_Summary.md
LICENSE
README.md
replit.md
```

________________

# AMAIMA Project Structure and Deployment Reference

## Document Overview

This comprehensive reference document provides a detailed mapping of the AMAIMA project structure to deployment configurations, enabling development teams to understand the relationship between source code organization and operational deployment. The document synthesizes the complete directory structure with deployment requirements, creating a unified reference that supports both day-to-day development operations and production deployment activities.

The AMAIMA project represents a sophisticated multi-platform AI orchestration system comprising a Python FastAPI backend, a Next.js 15 TypeScript frontend, and a native Android mobile application. These three primary components share common infrastructure concerns including authentication, observability, and deployment automation, while maintaining platform-specific implementation details appropriate to their respective technology stacks. Understanding this dual nature—shared architectural principles with platform-specific implementations—is essential for effective project navigation and deployment.

The directory structure reflects deliberate organizational decisions made during the project's development phase. Components are grouped by platform (backend, frontend, mobile) with shared resources organized separately in the docs and tests directories. This structure supports parallel development workflows where backend engineers, frontend developers, and mobile engineers can work within their respective domains while maintaining clear boundaries that prevent cross-contamination of platform-specific concerns. The preservation notes distributed throughout the structure identify components that contain novel intellectual property requiring protection during any code modification or redistribution activities.

---

## Project Root Organization

### Root Directory Contents

The AMAIMA project root directory establishes the top-level organization that separates platform-specific implementations from shared resources. This organizational pattern enables clear identification of component boundaries while maintaining accessibility to cross-cutting concerns such as documentation, testing infrastructure, and licensing information.

The root directory contains four primary entries that define the project's scope and operational context. The `amaima/backend` directory houses the Python FastAPI backend application implementing the core AI orchestration logic, model management, and API serving capabilities. This directory represents the computational heart of the AMAIMA system, containing the five crown-jewel modules that implement the novel architectural innovations distinguishing AMAIMA from commodity AI deployment solutions.

The `amaima/frontend` directory contains the Next.js 15 TypeScript application providing the web-based user interface for the AMAIMA platform. This application implements the complete user experience layer, including query submission interfaces, real-time response rendering, workflow management, and system monitoring dashboards. The frontend architecture leverages React 19 with TypeScript for type-safe development, Zustand for state management, and WebSocket connections for real-time communication with the backend.

The `amaima/mobile` directory contains the native Android application implemented in Kotlin with Jetpack Compose. This mobile client provides AMAIMA access for Android devices, implementing on-device TensorFlow Lite inference for complexity estimation, biometric authentication, and offline-first operation patterns that enable continued productivity during network interruptions. The mobile architecture follows Clean Architecture principles with clear separation between presentation, domain, and data layers.

The `amaima/tests` directory contains the comprehensive testing infrastructure supporting all three platform implementations. This directory follows Python pytest conventions for backend testing while maintaining compatibility with frontend and mobile testing requirements. The testing structure enables cross-platform test execution, shared fixtures, and unified coverage reporting.

Supporting entries at the root level include the `docs` directory containing architectural documentation, integration guides, and operational procedures; the `LICENSE` file establishing the project's custom licensing framework; and the `README.md` file providing entry-point documentation for project contributors. The `replit.md` file likely contains configuration notes for Replit cloud development environments, supporting collaborative development workflows.

### Documentation Structure

The `docs` directory provides comprehensive documentation organized by functional area. The `docs/executive-summary` subdirectory contains high-level documentation suitable for stakeholders requiring understanding of AMAIMA's business value and strategic positioning. The `AMAIMA_System_Executive_Summary.md` file synthesizes the platform's capabilities, market positioning, and acquisition-oriented valuation framework, providing context for business decision-makers.

The `docs/development-deployment` subdirectory contains operational documentation including the platform development and deployment strategy. The `AMAIMA_Platform_Development_&_Deployment_Strategy.md` file establishes the methodological framework guiding project development, including the hybrid approach combining human-defined core architecture with AI-assisted infrastructure development.

The `docs/integration` subdirectory contains technical integration documentation. The `AMAIMA_System_Integration_Guide.md` file provides comprehensive guidance for connecting the backend, frontend, and mobile components into a cohesive platform, including authentication protocols, WebSocket communication patterns, and data synchronization strategies.

The `docs/summary` subdirectory contains consolidated summary documentation. The `Backend_Frontend_Mobile_Integration_Summary.md` file provides an executive-level overview of the complete integration landscape, serving as a quick reference for understanding how platform components interconnect.

The `docs/charts` subdirectory contains visualization and documentation of system architecture. The `Charts.md` file likely documents architectural diagrams, data flow visualizations, and system interaction patterns that supplement the textual documentation with graphical representations of platform behavior.

### License and Configuration Files

The root-level `LICENSE` file establishes the custom multi-license framework governing AMAIMA distribution and use. This custom license explicitly protects the novel architectural elements while enabling community engagement and commercial sustainability. Understanding the license framework is essential for any deployment scenario, as it establishes the legal framework governing component modification, redistribution, and commercial utilization.

The `README.md` file provides entry-point documentation for project contributors, establishing development environment setup procedures, build processes, and contribution guidelines. This file serves as the starting point for new team members and should be maintained as the authoritative source for initial project setup procedures.

The `replit.md` file provides configuration documentation for Replit cloud development environments, enabling collaborative development workflows and continuous integration through the Replit platform. This file supports development scenarios where local environment setup is impractical or where distributed team collaboration requires cloud-hosted development infrastructure.

---

## Backend Directory Structure

### Core Application Components

The `amaima/backend` directory contains the complete Python FastAPI application implementing AMAIMA's core AI orchestration capabilities. The directory structure follows Python package conventions with the `app` subdirectory serving as the Python package root containing the application's core implementation. The preservation note in `PRESERVE_THESE.md` identifies this directory as containing novel intellectual property requiring protection during any code modification or distribution activities.

The `amaima/backend/app` directory contains the primary application code organized into functional subsystems. The `amaima/backend/app/core` subdirectory contains fundamental service implementations including the `production_api_server.py` file implementing the FastAPI application, the `progressive_model_loader.py` file implementing dynamic model loading with TensorRT optimization, and the `unified_smart_router.py` file implementing the five-level query complexity classification system that represents one of AMAIMA's foundational innovations.

The `amaima/backend/app/modules` subdirectory contains specialized module implementations including the `multi_layer_verification_engine.py` file implementing the four-stage verification pipeline (syntax, semantic, safety, and consistency verification) that provides enterprise-grade output validation. These core modules represent the computational heart of AMAIMA's value proposition, implementing the novel algorithms and processing logic that differentiate the platform from commodity AI deployment solutions.

### Application Organization

The `amaima/backend/routers` subdirectory contains FastAPI router implementations that define API endpoint groupings. The `query_router.py` file implements the query submission and management endpoints, defining the REST interface through which frontend and mobile clients interact with the AI orchestration capabilities. Router implementations follow FastAPI conventions, defining endpoint paths, request/response models, and dependency injection for shared functionality.

The `amaima/backend/middleware` subdirectory contains middleware implementations providing cross-cutting functionality. The `error_handler.py` file implements centralized error handling that ensures consistent error response formats across all API endpoints, improving client integration reliability and simplifying debugging operations.

The `amaima/backend/auth` subdirectory contains authentication and authorization implementations. The `token_validation.py` file implements JWT token validation with the RS256 signing algorithm, establishing the security framework that protects API access and enables session management across all platform components.

### Backend Documentation

The `amaima/backend/AMAIMA_Part_V_Comprehensive_Module_Integration_&_Final_Build_Specification.md` file provides detailed technical specification for the backend architecture, module organization, and build procedures. This document serves as the authoritative reference for backend implementation details, including the five-layer architecture, the 18 consolidated modules, and the production deployment requirements.

The `amaima/backend/PRESERVE_THESE.md` file documents the specific components within the backend directory that contain protected intellectual property. This preservation note establishes clear boundaries around which components must remain unaltered in any distribution or derivative work, ensuring that the most valuable architectural innovations remain under project control regardless of how the platform is licensed.

### Deployment Configuration Mapping

Deploying the backend requires understanding how the application structure maps to deployment artifacts. The production Dockerfile should be created in `amaima/backend/docker` following the multi-stage build pattern described in the deployment configuration section, with the build context set to the `amaima/backend` directory to access the complete application structure.

The backend configuration file (`amaima_config.yaml`) should be created in `amaima/backend/config` or deployed through the ConfigMap mechanism for Kubernetes deployments. This configuration file controls all runtime parameters including database connections, model paths, verification pipeline settings, and observability configuration.

Environment-specific overrides can be managed through environment variable injection during deployment, with the configuration file providing default values that can be overridden at deployment time. This pattern enables consistent base configurations across environments while supporting environment-specific customization for development, staging, and production scenarios.

---

## Frontend Directory Structure

### Application Source Organization

The `amaima/frontend` directory contains the complete Next.js 15 TypeScript application providing AMAIMA's web-based user interface. The `src` subdirectory contains the application source code, following Next.js App Router conventions for file-based routing and component organization. The preservation note in `amaima/frontend/PRESERVE_THESE.md` identifies the frontend components containing protected implementation details.

The `amaima/frontend/src/app` directory contains the primary application structure implementing routes, layouts, and page components. The `layout.tsx` file defines the root application layout including providers, global styles, and metadata configuration. The `page.tsx` file implements the application home page, serving as the entry point for authenticated users accessing the platform's main functionality.

The `globals.css` file defines global CSS styles and Tailwind CSS configurations implementing the platform's design system. The glassmorphism aesthetic referenced in the implementation guide is achieved through these global styles combined with Tailwind utility classes applied throughout the component structure.

### Core Component Architecture

The `amaima/frontend/src/app/core/components` directory contains the component library organized by functional area. The `ui` subdirectory contains base UI components including the `badge.tsx`, `button.tsx`, `card.tsx`, and `textarea.tsx` files implementing the fundamental interface elements used throughout the application. These components follow the design system specifications, ensuring visual consistency and providing shared behavior through composition.

The `dashboard` subdirectory contains components implementing the dashboard interface including the `SystemMonitor.tsx` file that renders real-time system metrics through visualization charts. The dashboard components provide the operational visibility required for monitoring platform health and query performance.

The `query` subdirectory contains components implementing the query submission and response interface. The `QueryInput.tsx` file implements the query entry interface with complexity estimation display, the `StreamingResponse.tsx` file implements real-time response rendering with Markdown support, the `CodeBlock.tsx` file implements syntax highlighting for code snippets, and the `QueryWithFile.tsx` file implements file attachment functionality for queries requiring document context.

### State Management and API Layer

The `amaima/frontend/src/app/core/lib` directory contains the core library implementations including state management, API clients, machine learning utilities, and WebSocket communication. The `api` subdirectory contains the API client implementation with the `client.ts` file providing the base HTTP client configuration, the `error-handler.ts` file implementing consistent error handling, and the `queries.ts` file defining typed API endpoints for query operations.

The `auth` subdirectory contains authentication implementations including the `auth-provider.tsx` file implementing the authentication context provider that manages user session state throughout the application. Authentication state flows through this provider to all components requiring user context.

The `ml` subdirectory contains machine learning utilities including the `complexity-estimator.ts` file implementing TensorFlow.js-based complexity classification for client-side query preview. This client-side complexity estimation enables users to understand query routing predictions before submission.

The `stores` subdirectory contains Zustand state management implementations including `useAuthStore.ts` for authentication state, `useQueryStore.ts` for query management state, and `useSystemStore.ts` for system metrics state. These stores provide reactive state management enabling efficient UI updates without unnecessary re-renders.

### WebSocket and Synchronization

The `amaima/frontend/src/app/core/lib/websocket` directory contains WebSocket communication implementations. The `WebSocketProvider.tsx` file implements the React context provider managing WebSocket connections, providing connection state and message distribution to consuming components. The `websocket-manager.ts` file implements the underlying WebSocket connection management including reconnection logic, message queuing, and heartbeat monitoring.

The `amaima/frontend/src/app/core/lib/sync` directory contains synchronization implementations for offline-first operation. The `sync-manager.ts` file implements the synchronization logic that coordinates local state with backend state, enabling continued operation during network interruptions and automatic synchronization when connectivity returns.

The `amaima/frontend/src/app/core/lib/upload` directory contains file upload implementations. The `file-uploader.ts` file implements the upload logic supporting chunked uploads for large files with progress tracking and retry capabilities.

### Utility Functions and Types

The `amaima/frontend/src/app/core/lib/utils` directory contains utility functions including the `cn.ts` file implementing class name composition for Tailwind CSS, the `format.ts` file implementing data formatting utilities, the `secure-storage.ts` file implementing encrypted local storage, and the `validation.ts` file implementing form validation logic.

The `amaima/frontend/src/app/core/hooks` directory contains custom React hooks including `useDebounce.ts` for debounced value updates, `useMLInference.ts` for machine learning inference integration, and `useQuery.ts` for query lifecycle management.

The `amaima/frontend/src/app/core/types` directory contains TypeScript type definitions establishing the type system for the frontend application. These types ensure type safety across the application while providing documentation for data structures and API contracts.

### Frontend Documentation

The `amaima/frontend/AMAIMA_Frontend_Complete_Implementation_Guide.md` file provides comprehensive documentation of the frontend architecture, component library, state management, and integration patterns. This document serves as the authoritative reference for frontend development and maintenance activities.

### Frontend Deployment Configuration

Deploying the frontend requires understanding the Next.js build output structure. The Dockerfile should be created in `amaima/frontend/docker` following the multi-stage build pattern, with the build context set to the `amaima/frontend` directory. The Next.js standalone output mode produces a minimal server.js file and static assets that can be served through the Nginx configuration provided in the deployment package.

The `next.config.js` file in `amaima/frontend` configures Next.js build options including output mode, image optimization, security headers, and webpack customization for TensorFlow.js compatibility. This configuration file should be deployed alongside the built application to ensure correct runtime behavior.

Environment variables for the frontend should be configured through the Next.js environment variable mechanism, with variables prefixed with `NEXT_PUBLIC_` being exposed to the browser client. The `NEXT_PUBLIC_API_URL` variable is critical for directing client API requests to the backend endpoint.

---

## Mobile Directory Structure

### Application Package Organization

The `amaima/mobile` directory contains the native Android application implemented in Kotlin with Jetpack Compose. The `app/src/main/java/com/amaima/app` directory follows the standard Android application package structure, implementing the complete mobile functionality following Clean Architecture principles. The preservation note in `amaima/mobile/AMAIMA_Android_Client_Complete_APK_Design_Specification.md` identifies protected mobile implementation details.

The `amaima/mobile/app/src/main/java/com/amaima/app` directory serves as the root package containing all application code. Subpackages organize functionality by architectural layer following domain-driven design principles that separate concerns and enable testability.

### Presentation Layer

The `amaima/mobile/app/src/main/java/com/amaima/app/presentation` directory contains presentation layer implementations following the MVVM (Model-View-ViewModel) pattern. The `AmaimaNavHost.kt` file implements the navigation graph using Jetpack Compose Navigation, defining routes and transitions between screens. The `HomeScreen.kt` file implements the home screen UI displaying system status, recent activity, and quick actions. The `QueryScreen.kt` file implements the query submission interface with text input, operation selection, and response display.

The `amaima/mobile/app/src/main/java/com/amaima/app/ui/query` directory contains query-related presentation components. The `QueryViewModel.kt` file implements the ViewModel managing query state, coordinating between the presentation layer and domain layer, and handling user interactions.

### Data Layer

The `amaima/mobile/app/src/main/java/com/amaima/app/data` directory contains data layer implementations managing local storage, network communication, and data access patterns. The `local` subdirectory contains Room database implementations including the `entity` subdirectory with `QueryEntity.kt` defining the database entity for query storage and `QueryRepositoryImpl.kt` implementing the repository pattern for query data access.

The `remote` subdirectory contains network implementations including the `api` subdirectory with `AmaimaApi.kt` defining the Retrofit API interface for REST communication. The `interceptor` subdirectory contains the `AuthInterceptor.kt` file implementing authentication header injection for API requests. The `websocket` subdirectory contains `AmaimaWebSocket.kt` implementing WebSocket communication for real-time updates.

The `repository` directory contains repository implementations including `AuthRepository.kt` implementing authentication data access. The `sync` directory contains synchronization implementations including `SyncWorker.kt` implementing background synchronization using WorkManager for offline-first operation.

### Domain Layer

The `amaima/mobile/app/src/main/java/com/amaima/app` root package contains domain layer interfaces and use cases that define the application's business logic independent of framework details. These interfaces define contracts that data layer implementations satisfy and that presentation layer components consume.

### Machine Learning Integration

The `amaima/mobile/app/src/main/java/com/amaima/app/ml` directory contains TensorFlow Lite integration. The `TensorFlowLiteManager.kt` file manages on-device machine learning models including model loading, inference execution, and resource cleanup. This implementation enables client-side complexity estimation and limited offline inference.

### Security Implementation

The `amaima/mobile/app/src/main/java/com/amaima/app/security` directory contains security implementations. The `BiometricAuthManager.kt` file implements biometric authentication using Android's BiometricPrompt API, providing secure device-level access control. The `EncryptedPreferences.kt` file implements encrypted shared preferences for secure credential storage using AES-256 encryption with hardware-backed key storage.

### Dependency Injection

The `amaima/mobile/app/src/main/java/com/amaima/app/di` directory contains dependency injection configuration. The `AppModule.kt` file configures Hilt dependency injection modules defining bindings for network clients, database instances, repository implementations, and use cases.

### Application Entry Point

The `amaima/mobile/app/src/main/java/com/amaima/app/AmaimaApplication.kt` file implements the Application class initializing dependency injection, crash reporting, analytics, and TensorFlow Lite model loading.

### Mobile Documentation

The `amaima/mobile/AMAIMA_Android_Client_Complete_APK_Design_Specification.md` file provides comprehensive documentation of the mobile architecture, Clean Architecture implementation, TensorFlow Lite integration, and security framework. This document serves as the authoritative reference for mobile development and maintenance activities.

### Mobile Build Configuration

The `amaima/mobile/app/src/main/java/com/amaima/app/settings/gradle.kt` file (likely a settings.gradle.kts file) configures the Gradle build system including plugin versions, repository configurations, and build variants. The `proguard-rules.pro` file configures ProGuard optimization rules for release builds.

Deploying the mobile application requires configuring the Gradle wrapper with appropriate JDK and Android SDK versions, generating a signed release APK for distribution, and configuring the GitHub Actions workflow for automated builds and Google Play deployment.

---

## Testing Infrastructure

### Test Directory Structure

The `amaima/tests` directory contains the comprehensive testing infrastructure supporting all platform components. The `conftest.py` file defines pytest fixtures providing test data, mock objects, and test utilities shared across test modules. This configuration enables consistent test execution while reducing duplication of setup code across test files.

The testing infrastructure supports multiple testing strategies appropriate to each platform. Backend tests use pytest with async support for testing FastAPI endpoints and asynchronous service methods. Frontend tests use Jest with React Testing Library for component unit testing and integration testing. Mobile tests use Android instrumented tests with JUnit and Espresso for UI testing.

### Integration Testing

The `amaima/frontend/tests/integration.spec.ts` file implements integration tests verifying frontend-backend interaction patterns. These tests verify authentication flows, query submission with streaming responses, and real-time update propagation through WebSocket connections. Integration tests provide confidence in system behavior without requiring full deployment to target environments.

---

## Deployment Path Mapping

### Backend Deployment Paths

Deploying the backend requires the following file mappings from the project structure to deployment locations:

The backend source code in `amaima/backend` should be built using the Dockerfile created in `amaima/backend/docker`. The build context should include the parent directory to access both the backend source and any shared configurations. The resulting container image should be tagged with the version identifier and pushed to the container registry configured in the CI/CD pipeline.

The backend configuration file should be created at `amaima/backend/config/amaima_config.yaml` or deployed through Kubernetes ConfigMap. This file controls all runtime parameters and should be customized for each deployment environment through environment-specific overrides.

The backend requires persistent storage for model caching, typically mounted at `/app/models` within the container. For Kubernetes deployments, this requires a PersistentVolumeClaim with appropriate capacity and storage class. For Docker Compose deployments, a named volume provides the same functionality.

### Frontend Deployment Paths

Deploying the frontend requires the following file mappings:

The frontend source code in `amaima/frontend` should be built using the Dockerfile created in `amaima/frontend/docker`. The Next.js standalone output produces a minimal Node.js server that requires the Nginx configuration for production serving. The build context should be the `amaima/frontend` directory.

The Nginx configuration should be created at `amaima/frontend/docker/nginx/default.conf` within the Docker build context. This configuration handles API proxying, WebSocket connections, and static asset serving for the production deployment.

Environment variables for the frontend, particularly `NEXT_PUBLIC_API_URL`, should be configured at deployment time through the CI/CD pipeline or container orchestration platform. These variables direct client requests to the appropriate backend endpoint.

### Mobile Deployment Paths

Deploying the mobile application requires the following steps:

Configure the Gradle wrapper by running `./gradlew wrapper` in the `amaima/mobile` directory with JDK 17 and Android SDK installed. This generates the Gradle wrapper scripts and version configuration enabling consistent builds across development environments.

Configure signing credentials by creating a keystore file and configuring the signing configuration in the `build.gradle.kts` file. The keystore credentials should be stored securely and referenced through environment variables or GitHub secrets for CI/CD builds.

Build the release APK by running `./gradlew assembleRelease` after configuring signing. The resulting APK is located at `app/build/outputs/apk/release/app-release.apk` and can be distributed through Google Play or enterprise deployment channels.

Configure the GitHub Actions workflow in `amaima/.github/workflows/android-ci.yml` to automate builds and enable Google Play deployment. This requires configuring Google Play service account credentials as GitHub secrets.

---

## Configuration File Reference

### Backend Configuration

The backend configuration file (`amaima_config.yaml`) establishes all runtime parameters for the AI orchestration platform. The configuration structure follows the architecture's five-layer design, with sections for each layer's components and their specific requirements.

The `app` section configures application-level parameters including name, version, environment, debug mode, and host bindings. The `database` section configures PostgreSQL connection parameters including connection pool settings. The `redis` section configures Redis connection parameters including connection pool and timeout settings.

The `jwt` section configures authentication parameters including the signing algorithm, token expiration times, and key paths. The `router` section configures the Smart Router Engine including complexity level definitions, model mappings, and caching parameters.

The `model_loader` section configures the Progressive Model Loader including cache directory, TensorRT settings, quantization options, and memory management parameters. The `verification` section configures the Multi-Layer Verification Engine including enabled verification stages, confidence thresholds, and content policies.

The `api` section configures the Production API Server including CORS settings, rate limiting, and request size limits. The `observability` section configures the Observability Framework including log level, metrics collection, and tracing parameters.

### Frontend Configuration

The frontend `next.config.js` file configures Next.js build options including output mode, environment variable exposure, image optimization, security headers, and webpack customization. This file should be deployed alongside the built application to ensure correct runtime behavior.

Environment variables in the frontend follow the Next.js convention where variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. Critical variables include `NEXT_PUBLIC_API_URL` directing client API requests and `NEXT_PUBLIC_APP_VERSION` enabling version display in the UI.

### Kubernetes Manifests

The Kubernetes manifests in the deployment package configure all cluster resources including namespaces, secrets, deployments, services, ingress, and horizontal pod autoscalers. These manifests reference container images built from the source code structure and configuration files documented above.

The namespace manifest creates the `amaima` namespace for platform components. Secret manifests configure database credentials and JWT keys. Deployment manifests configure container images, resource requests, health checks, and volume mounts. Service manifests expose deployments within the cluster. Ingress manifest configures external access with TLS termination.

### Docker Compose Configuration

The Docker Compose configuration in the deployment package orchestrates all services for local development and testing. This configuration references the Dockerfiles created from the source structure and configures environment variables, volume mounts, and dependency relationships.

The compose configuration should be placed at the project root or in a dedicated `deployments/docker` directory, with the build contexts configured to reference the source directories documented above.

---

## Best Practices and Maintenance

### Code Organization Principles

Maintaining the AMAIMA project requires adherence to the organizational principles established during initial development. Platform-specific code should remain within its respective directory (backend, frontend, mobile) without cross-contamination. Shared concerns should be managed through the documented interfaces without embedding platform-specific logic in shared locations.

The preservation notes identify components containing novel intellectual property. Any modifications to these components should be carefully reviewed to ensure that protected implementation details are not compromised. New features should be implemented in non-preserved components where possible, with preserved components reserved for modifications to core protected functionality.

### Documentation Maintenance

Documentation files should be updated alongside code changes to maintain accuracy. The preservation notes reference specific documentation files that should be reviewed when modifying protected components. The deployment documentation should be updated when deployment procedures change, ensuring that operational guidance remains accurate and actionable.

### Testing Requirements

All code changes should include appropriate test coverage. Backend changes should include unit tests in the `amaima/tests` directory. Frontend changes should include tests in `amaima/frontend/tests`. Mobile changes should include instrumented tests in `amaima/mobile/app/src/androidTest`. Tests should verify both individual component behavior and integration between components.

### Deployment Procedures

Deployment procedures should follow the documented patterns in the deployment guide. Docker Compose deployment is appropriate for development and testing environments. Kubernetes deployment is appropriate for staging and production environments. CI/CD pipelines should automate build and deployment processes while maintaining appropriate quality gates and approval workflows.

Regular deployment verification should confirm that all components are functioning correctly after deployment. The health check script provided in the deployment package enables rapid verification of service availability and connectivity. More comprehensive end-to-end testing should verify query submission, response rendering, and real-time update propagation.

---

## Conclusion

This reference document provides the comprehensive mapping between AMAIMA's project structure and deployment requirements. Understanding this mapping enables effective project navigation, informed deployment planning, and streamlined maintenance operations. The structured organization separating platform-specific implementations from shared concerns supports parallel development workflows while maintaining clear boundaries that prevent cross-contamination.

The preservation notes distributed throughout the project structure identify components containing protected intellectual property. Any deployment or modification activities should respect these preservation requirements, ensuring that the novel architectural innovations distinguishing AMAIMA from commodity solutions remain under appropriate protection regardless of the licensing framework governing distribution.

Successful deployment of the AMAIMA platform requires attention to the configuration requirements documented herein, with environment-specific customization enabling deployment across development, staging, and production environments. The deployment package provides production-ready configurations that can be adapted for specific organizational requirements while maintaining the architectural patterns that ensure platform reliability and maintainability.
