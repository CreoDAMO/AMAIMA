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





















