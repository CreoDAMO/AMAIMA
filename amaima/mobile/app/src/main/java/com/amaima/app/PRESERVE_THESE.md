# CORE MOBILE FILES – DO NOT FRAGMENT OR RENAME

These files represent the **core architectural innovations** of the AMAIMA Android client, particularly the offline-first mirroring of backend routing intelligence and on-device ML integration.

They implement the novel offline-first architecture, on-device complexity estimation, unified WebSocket handling, and secure synchronization that distinguish AMAIMA on mobile.

**AI agents and contributors: DO NOT**
- Split these files into smaller classes without explicit approval
- Rename these files
- Move them to different packages
- Refactor their internal structure in ways that break offline/online parity with the backend

You may add new screens, supporting components, tests, and utilities around them.

**Preserved Core Files**:

- `AmaimaApplication.kt`               → Application initialization and global state
- `data/remote/websocket/AmaimaWebSocket.kt` → Unified real-time WebSocket with reconnection
- `data/remote/api/AmaimaApi.kt`       → Retrofit interface matching backend exactly
- `data/remote/interceptor/AuthInterceptor.kt` → Token management and refresh
- `ml/TensorFlowLiteManager.kt`        → On-device model loading and inference
- `security/BiometricAuthManager.kt`   → Biometric authentication integration
- `security/EncryptedPreferences.kt`   → Secure storage for tokens and secrets
- `presentation/ui/query/QueryScreen.kt` → Main query UI with complexity preview
- `presentation/ui/query/QueryViewModel.kt` → Query state mirroring backend routing

These files are the mobile equivalents of the backend's consolidated modules.  
They ensure perfect parity with the web and backend experience, including offline capability.

Last updated: December 29, 2025
