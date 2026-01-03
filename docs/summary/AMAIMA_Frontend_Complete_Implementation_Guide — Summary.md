# AMAIMA Frontend Complete Implementation Guide — Summary

## Overview

The AMAIMA Frontend is a comprehensive Next.js 15 application built with React 19 and TypeScript, designed to provide a seamless interface for the AMAIMA AI system. This implementation delivers approximately 8,000 lines of production code featuring a modern glassmorphism aesthetic, real-time WebSocket communication, client-side machine learning via TensorFlow.js, and enterprise-grade security measures. The frontend integrates directly with the Python FastAPI backend and Android client applications, providing a unified experience across all platforms.

The architecture follows the Next.js App Router pattern with a clear separation between public marketing pages and protected dashboard routes. State management leverages Zustand with encrypted persistent storage, while data fetching utilizes TanStack Query for caching and synchronization. Real-time capabilities are provided through a custom WebSocket implementation with automatic reconnection, message queuing, and heartbeat mechanisms.

## Architecture and Technology Stack

### Core Framework and Dependencies

The application uses Next.js 15 with React 19, taking advantage of the App Router for file-based routing and server components where appropriate. The technology stack includes Tailwind CSS for styling with custom glassmorphism effects through the shadcn/ui design pattern, Framer Motion for animations, Recharts for data visualization, and TanStack Query for asynchronous data management. The dependency structure is organized into production dependencies including React ecosystem packages, UI component libraries, and data visualization tools, while development dependencies encompass TypeScript, testing frameworks, and build tools.

### Project Structure

The application follows a feature-based organization pattern. The app directory contains route groups for authentication and dashboard layouts, with API routes for backend proxying. The components directory houses reusable UI elements in the ui subdirectory, feature-specific components organized by domain (query, workflow, dashboard), and shared components for common patterns. The lib directory contains API client modules, Zustand stores, ML utilities, WebSocket providers, and utility functions. Custom hooks provide reusable logic for authentication, data fetching, media queries, and click-outside detection.

## Core Type System

The type definitions establish a comprehensive contract for the application's data structures. Query types define the query lifecycle including operation types (general, code_generation, analysis, translation, creative), status tracking (pending, processing, completed, failed), and metadata for complexity scoring and token estimation. Workflow types define step-based automation with configurable step types, parameters, and dependency management. User types handle authentication state, role-based access (user, admin, premium), and preference management. API response types provide standardized success/error handling with rate limit information. WebSocket message types enable real-time updates for query progress, workflow status, and system metrics.

## State Management and Security

### Authentication and User State

The authentication system combines Zustand state management with encrypted localStorage persistence using CryptoJS. The auth store maintains user information, JWT tokens, and authentication status with automatic initialization from secure storage on application load. The login and register mutations interact with the backend authentication endpoints, storing credentials securely upon successful authentication. Logout clears all sensitive data from both state and storage.

### Query and System State

The query store tracks active and historical queries with support for streaming response updates. Methods exist for adding queries, updating status, appending response chunks, and managing the active query for display. The system store maintains real-time metrics including CPU usage, memory consumption, active query counts, and per-model status information. This state is populated primarily through WebSocket messages from the backend.

### Secure Storage Utility

The secure storage wrapper encrypts all data before storing in localStorage using AES encryption with a dynamically generated encryption key. The key is stored separately from encrypted data and regenerated if not found. This approach protects sensitive authentication tokens and user data even if the browser's localStorage is compromised.

## Real-Time Communication

### WebSocket Provider Architecture

The WebSocket provider implements a robust real-time communication layer with several key features. Connection management handles automatic reconnection with exponential backoff up to five attempts, with successful reauthentication on reconnection. Message processing routes incoming messages to appropriate handlers based on message type, updating query status, system metrics, and model availability. The heartbeat system sends ping messages every 30 seconds to detect connection failures and measure latency for connection quality assessment.

### Message Queue and Offline Support

When the WebSocket connection is unavailable, messages are queued locally and sent automatically upon reconnection. This ensures that critical operations like query subscriptions are not lost during network interruptions. The connection quality indicator provides visual feedback on latency status (excellent, good, poor, disconnected).

## API Layer

### Client Architecture

The API client provides a typed wrapper around fetch with automatic authentication header injection, error handling with standardized error response formats, and request/response interception capabilities. Each domain (queries, workflows, users, models) has dedicated API modules with typed methods that return standardized response objects containing success indicators, data payloads, and metadata.

### Data Fetching Strategy

TanStack Query handles all server state with custom hooks for each domain. The useSubmitQuery hook implements optimistic updates by creating a temporary query entry immediately while the actual submission processes in the background. Query invalidation ensures data freshness after mutations. Background refetching keeps lists synchronized with server state.

## Machine Learning Integration

### Client-Side Complexity Estimation

The complexity estimator uses TensorFlow.js to classify queries into five complexity levels (TRIVIAL, SIMPLE, MODERATE, COMPLEX, EXPERT) based on textual analysis. The model receives preprocessed text vectors and outputs probability distributions across complexity classes with associated confidence scores. The system uses rule-based fallback estimation when the ML model is unavailable, analyzing word count, pattern matching for complexity indicators, and domain-specific keywords.

### Token Estimation

The system estimates token counts for billing and model selection purposes using a simple word-based approximation (approximately 1.3 tokens per word) suitable for the intended precision requirements. This feeds into model selection logic for cost optimization.

## UI Component System

### Base Components

The UI component library implements a glassmorphism design language with backdrop blur effects, subtle borders, and gradient backgrounds. Core components include Button with multiple variants (default, neon, glass, destructive), Card containers with consistent styling, Textarea with focus states, Badge for status indicators, and Input fields. All components support dark mode through Tailwind's color system with CSS variables for theming.

### Feature Components

QueryInput combines a textarea for query entry, operation selector buttons, real-time complexity estimation display, and submission controls. StreamingResponse renders query results with Markdown support, syntax highlighting for code blocks, status indicators, and feedback collection. SystemMonitor displays real-time metrics with sparkline indicators, area charts for resource usage, and line charts for query throughput. The CodeBlock component provides syntax highlighting with copy functionality and language badges.

## Dashboard and Workflow System

### Dashboard Layout

The dashboard provides a persistent sidebar navigation with user profile dropdown, connection status indicator, and notification controls. Protected routes redirect unauthenticated users to the login page. The layout maintains authentication state across navigations and provides responsive design for mobile devices with collapsible sidebar.

### Workflow Builder

The workflow builder enables visual creation of automated query pipelines using drag-and-drop functionality via dnd-kit. Supported step types include Query steps for AI processing, Condition steps for branching logic, Loop steps for iteration, Function steps for custom operations, and API Call steps for external service integration. Each step type has specific configuration options appropriate to its function.

## Security Implementation

### Authentication Middleware

The middleware protects routes by verifying JWT tokens on each request, redirecting unauthenticated users to login, and redirecting authenticated users away from auth pages. Security headers are added to all responses including X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, and Content-Security-Policy.

### Encrypted Storage

All authentication data and sensitive user information is encrypted before storage using AES-256 encryption with unique per-session keys. This protects credentials even if local storage is accessed by malicious scripts.

## Deployment and Operations

### Docker Configuration

The multi-stage Dockerfile optimizes production deployment by separating dependency installation from build compilation and using a minimal Node.js Alpine image for the final runtime. The builder stage compiles the Next.js application in standalone mode, and the runner stage executes the compiled output with appropriate security context.

### Testing Infrastructure

Jest configuration with React Testing Library enables component unit testing, integration testing, and user event simulation. Custom matchers extend expect capabilities for common assertions. The setup file configures DOM mocks for JSDOM compatibility.

## Performance Characteristics

The frontend targets specific performance metrics including sub-second initial page loads through static generation where possible, sub-50ms route transitions via Next.js pre-fetching, real-time updates with WebSocket message latency under 200ms, and smooth 60fps animations using Framer Motion's optimized animation engine. Client-side complexity estimation completes within 100ms for typical query lengths, enabling responsive complexity indicators without perceptible delay.
