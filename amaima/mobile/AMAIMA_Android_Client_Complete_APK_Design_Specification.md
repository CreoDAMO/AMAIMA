# **AMAIMA Android Client Complete APK Design Specification**

## Executive Overview

This document presents the comprehensive design for the AMAIMA Android mobile application, a native client that provides secure, real-time access to the Advanced Multimodal AI Model Architecture system from mobile devices. The APK bridges the gap between the powerful Python-based backend infrastructure and mobile users, enabling query submission, workflow management, real-time monitoring, and on-device intelligence augmentation. The design leverages modern Android development practices including Kotlin, Jetpack Compose, and Clean Architecture to deliver a responsive, maintainable, and secure mobile experience.

The Android client serves as a critical access point for the AMAIMA ecosystem, supporting both connected and offline operation modes. Users can submit queries that are routed through the intelligent backend system, receive responses with full multimedia support, manage complex workflows, and provide feedback that contributes to the continuous learning pipeline. The application also implements on-device machine learning capabilities using TensorFlow Lite, enabling preprocessing, complexity estimation, and limited offline inference for specific model types.

The architecture prioritizes security at every layer, from secure communication protocols to local data encryption and biometric authentication. The application integrates seamlessly with the existing backend infrastructure, consuming REST APIs and WebSocket streams to deliver real-time updates while implementing intelligent caching and synchronization strategies for unreliable network conditions common in mobile environments.

## 1. System Architecture

### 1.1 High-Level Architecture

The AMAIMA Android client follows a multi-layer architecture that separates concerns, enables testing, and facilitates maintenance. The presentation layer handles UI rendering and user interactions using Jetpack Compose. The domain layer encapsulates business logic and use cases following Clean Architecture principles. The data layer manages local storage, network communication, and repository implementations. The infrastructure layer provides cross-cutting concerns including authentication, logging, and error handling.

The application communicates with the AMAIMA backend through a combination of REST APIs for standard request-response operations and WebSocket connections for real-time streaming. An intelligent caching layer stores frequently accessed data locally using Room database, enabling offline access to recent queries, workflows, and system status information. Background synchronization using WorkManager ensures data consistency when connectivity is restored.

On-device machine learning capabilities are provided through TensorFlow Lite models that perform query preprocessing, complexity estimation, and support for a limited subset of models in offline mode. These models are downloaded on-demand and updated through the application's update mechanism, ensuring users have access to the latest on-device capabilities without requiring a full APK update.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AMAIMA Android Client                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      Presentation Layer                        │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │  │
│  │  │   Home    │  │   Query   │  │  Workflow │  │  Profile  │  │  │
│  │  │   Screen  │  │   Screen  │  │  Screen   │  │   Screen  │  │  │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │  │
│  │        │              │              │              │        │  │
│  │  ┌─────┴──────────────┴──────────────┴──────────────┴─────┐  │  │
│  │  │              Jetpack Compose UI Framework               │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────┬───────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────┴───────────────────────────────┐  │
│  │                        Domain Layer                          │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │  │
│  │  │   Query   │  │ Workflow  │  │   User    │  │  System   │  │  │
│  │  │   UseCase │  │ UseCase   │  │ UseCase   │  │ UseCase   │  │  │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │  │
│  │        │              │              │              │        │  │
│  │  ┌─────┴──────────────┴──────────────┴──────────────┴─────┐  │  │
│  │  │           Clean Architecture Business Logic             │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────┬───────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────┴───────────────────────────────┐  │
│  │                         Data Layer                           │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │  │
│  │  │  Query    │  │ Workflow  │  │  Auth     │  │  Cache    │  │  │
│  │  │ Repository│  │ Repository│  │ Repository│  │ Repository│  │  │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │  │
│  │        │              │              │              │        │  │
│  │  ┌─────┴──────────────┴──────────────┴──────────────┴─────┐  │  │
│  │  │              Room Database & Network API                │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────┬───────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────┴───────────────────────────────┐  │
│  │                     Infrastructure Layer                     │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │  │
│  │  │  Retrofit │  │WebSocket  │  │TensorFlow │  │Security   │  │  │
│  │  │  Client   │  │ Handler   │  │   Lite    │  │  Manager  │  │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS / WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AMAIMA Backend Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Smart Router │  │  MCP Server  │  │    NeMo      │              │
│  │    Engine    │  │              │  │  Integration │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Design Principles

The Android client design adheres to several foundational principles that ensure code quality, maintainability, and user satisfaction. The principle of unidirectional data flow ensures that data changes propagate through a predictable path, making the application easier to debug and reason about. State management follows the single source of truth pattern, where the UI state is derived from immutable data structures that represent the current state of the application.

Dependency injection through Hilt provides testable, modular code by externalizing object creation and lifecycle management. This approach enables easy mocking of dependencies during testing and facilitates swapping implementations for different build variants. The application follows the recommendation to expose only what is necessary through carefully designed public APIs, keeping implementation details hidden from consumers.

Battery efficiency is a critical consideration given the mobile context. The application implements aggressive lazy loading, minimizes background network requests, and uses batched synchronization to reduce radio usage. Location and sensor access are minimized to only essential features with clear user consent. The design includes progressive enhancement patterns where features degrade gracefully when network connectivity is unavailable or when device capabilities are limited.

### 1.3 Technical Stack Selection

The technical stack represents the current best practices for Android development as of 2025, balancing stability with access to modern language features and frameworks. Kotlin serves as the primary development language, leveraging its null safety, coroutines, and extension functions to write concise, expressive code. The choice of Kotlin also enables seamless interoperability with existing Java libraries and the extensive Android ecosystem.

Jetpack Compose provides the UI framework, enabling declarative UI development that eliminates the verbosity of XML layouts while providing better performance through optimized recomposition. The Compose navigation component handles screen transitions with type-safe arguments, reducing runtime navigation errors. Material 3 design components ensure a consistent, accessible user interface that follows platform guidelines while maintaining the AMAIMA brand identity.

The networking stack uses Retrofit for REST API communication with Moshi for JSON serialization, providing compile-time type safety for network responses. OkHttp handles the underlying HTTP client with support for certificate pinning, connection pooling, and request interceptors. WebSocket communication uses a dedicated library that integrates with the coroutine-based architecture, enabling clean asynchronous handling of streaming data.

## 2. Application Structure

### 2.1 Package Organization

The package structure follows domain-driven design principles, organizing code by feature rather than technical layer. This organization facilitates parallel development, enables scoped refactoring, and makes it easier to understand the functionality associated with each feature area. The root packages establish clear boundaries between presentation, domain, and data layers while allowing for shared utilities that span multiple concerns.

```
com.amaima.app
├── data
│   ├── local
│   │   ├── dao
│   │   │   ├── QueryDao.kt
│   │   │   ├── WorkflowDao.kt
│   │   │   └── UserDao.kt
│   │   ├── entity
│   │   │   ├── QueryEntity.kt
│   │   │   ├── WorkflowEntity.kt
│   │   │   └── UserEntity.kt
│   │   └── database
│   │       └── AmaimaDatabase.kt
│   ├── remote
│   │   ├── api
│   │   │   ├── AmaimaApi.kt
│   │   │   └── dto
│   │   │       ├── QueryDto.kt
│   │   │       └── WorkflowDto.kt
│   │   ├── interceptor
│   │   │   └── AuthInterceptor.kt
│   │   └── websocket
│   │       └── AmaimaWebSocket.kt
│   ├── repository
│   │   ├── QueryRepositoryImpl.kt
│   │   └── WorkflowRepositoryImpl.kt
│   └── mapper
│       └── DtoMapper.kt
├── domain
│   ├── model
│   │   ├── Query.kt
│   │   ├── Workflow.kt
│   │   └── User.kt
│   ├── repository
│   │   ├── QueryRepository.kt
│   │   └── WorkflowRepository.kt
│   └── usecase
│       ├── query
│       │   ├── SubmitQueryUseCase.kt
│       │   └── GetQueryHistoryUseCase.kt
│       └── workflow
│           ├── ExecuteWorkflowUseCase.kt
│           └── GetWorkflowStatusUseCase.kt
├── presentation
│   ├── ui
│   │   ├── home
│   │   │   ├── HomeScreen.kt
│   │   │   ├── HomeViewModel.kt
│   │   │   └── HomeState.kt
│   │   ├── query
│   │   │   ├── QueryScreen.kt
│   │   │   ├── QueryViewModel.kt
│   │   │   └── QueryState.kt
│   │   ├── workflow
│   │   │   ├── WorkflowScreen.kt
│   │   │   ├── WorkflowViewModel.kt
│   │   │   └── WorkflowState.kt
│   │   └── components
│   │       ├── QueryInput.kt
│   │       ├── ResponseDisplay.kt
│   │       └── LoadingIndicator.kt
│   ├── navigation
│   │   ├── Screen.kt
│   │   └── AmaimaNavHost.kt
│   └── theme
│       ├── Color.kt
│       ├── Type.kt
│       └── Theme.kt
├── di
│   ├── AppModule.kt
│   ├── NetworkModule.kt
│   └── DatabaseModule.kt
├── ml
│   ├── TensorFlowLiteManager.kt
│   ├── OnDeviceModel.kt
│   └── ModelDownloader.kt
├── security
│   ├── BiometricManager.kt
│   ├── EncryptedPreferences.kt
│   └── CertificatePinning.kt
├── util
│   ├── NetworkMonitor.kt
│   ├── Result.kt
│   └── Extensions.kt
└── AmaimaApplication.kt
```

### 2.2 Core Application Class

The Application class initializes the dependency injection framework, configures global application state, and sets up crash reporting and analytics. The onCreate method performs initialization tasks that must complete before any activity starts, including loading the TensorFlow Lite models and establishing the database connection. The application class also registers lifecycle callbacks to monitor activity lifecycle events for resource management purposes.

```kotlin
class AmaimaApplication : Application() {

    lateinit var appContainer: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        
        initializeDependencyInjection()
        initializeCrashReporting()
        initializeAnalytics()
        initializeMlCapabilities()
        
        registerActivityLifecycleCallbacks(ActivityLifecycleHandler())
    }

    private fun initializeDependencyInjection() {
        appContainer = AppContainer(this)
    }

    private fun initializeCrashReporting() {
        if (BuildConfig.DEBUG.not()) {
            Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
                CrashReporter.reportException(throwable)
                DefaultUncaughtExceptionHandler.uncaughtException(thread, throwable)
            }
        }
    }

    private fun initializeAnalytics() {
        Analytics.initialize(this)
        Analytics.trackEvent(AnalyticsEvent.APP_OPENED)
    }

    private fun initializeMlCapabilities() {
        CoroutineScope(Dispatchers.Default).launch {
            try {
                val mlManager = appContainer.mlManager
                mlManager.loadDefaultModels()
                Log.d(TAG, "ML capabilities initialized successfully")
            } catch (e: Exception) {
                Log.w(TAG, "Failed to initialize ML capabilities", e)
            }
        }
    }

    companion object {
        private const val TAG = "AmaimaApplication"
        
        @Volatile
        private var instance: AmaimaApplication? = null
        
        fun getInstance(): AmaimaApplication {
            return instance ?: throw IllegalStateException(
                "Application not initialized"
            )
        }
    }
}
```

### 2.3 Dependency Injection Configuration

Hilt serves as the dependency injection framework, providing compile-time dependency resolution with zero runtime overhead for simple injections. The module structure defines bindings for different abstraction levels, from network clients and database instances to repository implementations and use cases. Build variant-specific modules enable environment-specific configurations for debug, staging, and production builds.

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideContext(@ApplicationContext context: Context): Context {
        return context.applicationContext
    }

    @Provides
    @Singleton
    fun provideNetworkMonitor(@ApplicationContext context: Context): NetworkMonitor {
        return NetworkMonitor(context)
    }

    @Provides
    @Singleton
    fun provideEncryptedPreferences(
        @ApplicationContext context: Context
    ): EncryptedPreferences {
        return EncryptedPreferences(context)
    }
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        certificatePinning: CertificatePinning
    ): OkHttpClient {
        return OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) {
                    HttpLoggingInterceptor.Level.BODY
                } else {
                    HttpLoggingInterceptor.Level.NONE
                }
            })
            .certificatePinner(certificatePinning.getCertificatePinner())
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .pingInterval(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        moshi: Moshi
    ): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
    }

    @Provides
    @Singleton
    fun provideAmaimaApi(retrofit: Retrofit): AmaimaApi {
        return retrofit.create(AmaimaApi::class.java)
    }

    @Provides
    @Singleton
    fun provideWebSocketClient(
        okHttpClient: OkHttpClient
    ): AmaimaWebSocket {
        return AmaimaWebSocket(okHttpClient)
    }

    @Provides
    @Singleton
    fun provideMoshi(): Moshi {
        return Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()
    }
}

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context
    ): AmaimaDatabase {
        return Room.databaseBuilder(
            context,
            AmaimaDatabase::class.java,
            "amaima_database"
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    fun provideQueryDao(database: AmaimaDatabase): QueryDao {
        return database.queryDao()
    }

    @Provides
    fun provideWorkflowDao(database: AmaimaDatabase): WorkflowDao {
        return database.workflowDao()
    }

    @Provides
    fun provideUserDao(database: AmaimaDatabase): UserDao {
        return database.userDao()
    }
}
```

## 3. Network Layer Implementation

### 3.1 REST API Client

The REST API client provides type-safe access to backend endpoints with automatic error handling, retry logic, and response mapping. Retrofit interfaces define the endpoints with compile-time verification of request paths, parameters, and response types. The API design mirrors the backend specification, providing consistent access to query processing, workflow management, and system monitoring capabilities.

```kotlin
interface AmaimaApi {

    @POST("/v1/query")
    suspend fun submitQuery(
        @Body request: QueryRequestDto
    ): Response<QueryResponseDto>

    @POST("/v1/workflow")
    suspend fun executeWorkflow(
        @Body request: WorkflowRequestDto
    ): Response<WorkflowResponseDto>

    @POST("/v1/feedback")
    suspend fun submitFeedback(
        @Body request: FeedbackRequestDto
    ): Response<Unit>

    @GET("/v1/models")
    suspend fun getAvailableModels(): Response<List<ModelInfoDto>>

    @GET("/v1/stats")
    suspend fun getSystemStats(): Response<SystemStatsDto>

    @GET("/health")
    suspend fun healthCheck(): Response<HealthResponseDto>
}

data class QueryRequestDto(
    @Json(name = "query") val query: String,
    @Json(name = "operation") val operation: String = "general",
    @Json(name = "file_types") val fileTypes: List<String>? = null,
    @Json(name = "user_id") val userId: String? = null,
    @Json(name = "preferences") val preferences: Map<String, Any>? = null
)

data class QueryResponseDto(
    @Json(name = "response_id") val responseId: String,
    @Json(name = "response_text") val responseText: String,
    @Json(name = "model_used") val modelUsed: String,
    @Json(name = "routing_decision") val routingDecision: RoutingDecisionDto,
    @Json(name = "confidence") val confidence: Float,
    @Json(name = "latency_ms") val latencyMs: Float,
    @Json(name = "timestamp") val timestamp: String
)

data class RoutingDecisionDto(
    @Json(name = "execution_mode") val executionMode: String,
    @Json(name = "model_size") val modelSize: String,
    @Json(name = "complexity") val complexity: String,
    @Json(name = "security_level") val securityLevel: String,
    @Json(name = "confidence") val confidence: Float,
    @Json(name = "estimated_latency_ms") val estimatedLatencyMs: Float,
    @Json(name = "estimated_cost") val estimatedCost: Float,
    @Json(name = "fallback_chain") val fallbackChain: List<String>
)

data class WorkflowRequestDto(
    @Json(name = "workflow_id") val workflowId: String,
    @Json(name = "steps") val steps: List<WorkflowStepDto>,
    @Json(name = "context") val context: Map<String, Any>? = null
)

data class WorkflowStepDto(
    @Json(name = "step_id") val stepId: String,
    @Json(name = "step_type") val stepType: String,
    @Json(name = "parameters") val parameters: Map<String, Any>,
    @Json(name = "dependencies") val dependencies: List<String>? = null
)

data class WorkflowResponseDto(
    @Json(name = "workflow_id") val workflowId: String,
    @Json(name = "status") val status: String,
    @Json(name = "results") val results: List<WorkflowResultDto>,
    @Json(name = "total_steps") val totalSteps: Int,
    @Json(name = "completed_steps") val completedSteps: Int,
    @Json(name = "duration_ms") val durationMs: Float
)

data class WorkflowResultDto(
    @Json(name = "step_id") val stepId: String,
    @Json(name = "step_type") val stepType: String,
    @Json(name = "status") val status: String,
    @Json(name = "output") val output: String?
)
```

### 3.2 WebSocket Handler

The WebSocket handler provides real-time communication capabilities for streaming query responses and workflow updates. The implementation integrates with coroutines to provide a suspending interface for sending messages and receiving updates. Automatic reconnection handles network interruptions with exponential backoff to prevent server overload during extended outages.

```kotlin
class AmaimaWebSocket(
    private val okHttpClient: OkHttpClient
) {
    private var webSocket: WebSocket? = null
    private var listener: AmaimaWebSocketListener? = null
    private var reconnectAttempts = 0
    private val maxReconnectAttempts = 5
    private val baseReconnectDelay = 1000L

    private val _messageFlow = MutableSharedFlow<WebSocketMessage>(extraBufferCapacity = 64)
    val messageFlow: Flow<WebSocketMessage> = _messageFlow.asSharedFlow()

    sealed class WebSocketMessage {
        data class QueryUpdate(val data: QueryUpdateDto) : WebSocketMessage()
        data class WorkflowUpdate(val data: WorkflowUpdateDto) : WebSocketMessage()
        data class ConnectionState(val state: ConnectionState) : WebSocketMessage()
        data class Error(val message: String) : WebSocketMessage()
    }

    enum class ConnectionState {
        CONNECTING, CONNECTED, DISCONNECTED, RECONNECTING, FAILED
    }

    fun connect(authToken: String) {
        if (webSocket != null) {
            return
        }

        val client = okHttpClient.newBuilder()
            .pingInterval(30, TimeUnit.SECONDS)
            .build()

        val request = Request.Builder()
            .url("${BuildConfig.WS_BASE_URL}/v1/ws/query")
            .addHeader("Authorization", "Bearer $authToken")
            .build()

        listener = AmaimaWebSocketListener(
            onOpen = { webSocket ->
                this.webSocket = webSocket
                reconnectAttempts = 0
                CoroutineScope(Dispatchers.IO).launch {
                    _messageFlow.emit(WebSocketMessage.ConnectionState(ConnectionState.CONNECTED))
                }
            },
            onMessage = { message ->
                parseMessage(message)
            },
            onClosing = { code, reason ->
                CoroutineScope(Dispatchers.IO).launch {
                    _messageFlow.emit(WebSocketMessage.ConnectionState(ConnectionState.DISCONNECTED))
                }
            },
            onClosed = { code, reason ->
                webSocket = null
            },
            onFailure = { exception ->
                handleConnectionFailure(exception)
            }
        )

        webSocket = client.newWebSocket(request, listener!!)
        CoroutineScope(Dispatchers.IO).launch {
            _messageFlow.emit(WebSocketMessage.ConnectionState(ConnectionState.CONNECTING))
        }
    }

    private fun parseMessage(message: String) {
        try {
            val jsonObject = Json.parseToJsonElement(message).jsonObject
            val messageType = jsonObject["type"]?.jsonPrimitive?.contentOrNull

            val coroutineScope = CoroutineScope(Dispatchers.IO)
            when (messageType) {
                "query_update" -> {
                    val data = Json.decodeFromString<QueryUpdateDto>(
                        jsonObject["data"]?.jsonObject.toString()
                    )
                    coroutineScope.launch {
                        _messageFlow.emit(WebSocketMessage.QueryUpdate(data))
                    }
                }
                "workflow_update" -> {
                    val data = Json.decodeFromString<WorkflowUpdateDto>(
                        jsonObject["data"]?.jsonObject.toString()
                    )
                    coroutineScope.launch {
                        _messageFlow.emit(WebSocketMessage.WorkflowUpdate(data))
                    }
                }
            }
        } catch (e: Exception) {
            CoroutineScope(Dispatchers.IO).launch {
                _messageFlow.emit(WebSocketMessage.Error("Failed to parse message: ${e.message}"))
            }
        }
    }

    private fun handleConnectionFailure(exception: Exception) {
        webSocket = null
        CoroutineScope(Dispatchers.IO).launch {
            _messageFlow.emit(WebSocketMessage.ConnectionState(ConnectionState.RECONNECTING))
        }

        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++
            val delay = baseReconnectDelay * (2.0.pow(reconnectAttempts - 1)).toLong()
            CoroutineScope(Dispatchers.IO).launch {
                delay(delay)
                reconnect()
            }
        } else {
            CoroutineScope(Dispatchers.IO).launch {
                _messageFlow.emit(WebSocketMessage.ConnectionState(ConnectionState.FAILED))
            }
        }
    }

    fun sendQueryRequest(request: StreamingQueryRequest) {
        webSocket?.send(Json.encodeToString(request))
    }

    fun disconnect() {
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
        reconnectAttempts = maxReconnectAttempts + 1
    }

    private fun reconnect() {
        val encryptedPrefs = EncryptedPreferences.getInstance()
        val token = encryptedPrefs.getAuthToken()
        if (token != null) {
            connect(token)
        }
    }
}

private class AmaimaWebSocketListener(
    private val onOpen: (WebSocket) -> Unit,
    private val onMessage: (String) -> Unit,
    private val onClosing: (Int, String) -> Unit,
    private val onClosed: (Int, String) -> Unit,
    private val onFailure: (Exception) -> Unit
) : WebSocketListener() {

    override fun onOpen(webSocket: WebSocket, response: Response) {
        onOpen(webSocket)
    }

    override fun onMessage(webSocket: WebSocket, text: String) {
        onMessage(text)
    }

    override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
        onClosing(code, reason)
    }

    override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
        onClosed(code, reason)
    }

    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
        onFailure(t as Exception)
    }
}
```

### 3.3 Authentication Interceptor

The authentication interceptor manages API authentication by automatically attaching tokens to requests and handling token refresh scenarios. The implementation uses a lazy refresh pattern where a single refresh operation serves multiple concurrent requests, preventing token refresh storms during startup or authentication expiry events.

```kotlin
class AuthInterceptor(
    private val encryptedPreferences: EncryptedPreferences,
    private val authRepository: AuthRepository
) : Interceptor {

    companion object {
        private const val AUTH_HEADER = "Authorization"
        private const val BEARER_PREFIX = "Bearer "
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()

        if (originalRequest.url.encodedPath.contains("/auth/")) {
            return chain.proceed(originalRequest)
        }

        val token = encryptedPreferences.getAuthToken()
        if (token == null) {
            return chain.proceed(originalRequest)
        }

        val authenticatedRequest = originalRequest.newBuilder()
            .header(AUTH_HEADER, "$BEARER_PREFIX$token")
            .build()

        val response = chain.proceed(authenticatedRequest)

        when (response.code) {
            401 -> {
                response.close()
                return handleUnauthorized(authenticatedRequest, chain)
            }
            403 -> {
                response.close()
                return Response.Builder()
                    .request(originalRequest)
                    .protocol(Protocol.HTTP_1_1)
                    .code(403)
                    .message("Access forbidden")
                    .build()
            }
        }

        return response
    }

    private suspend fun handleUnauthorized(
        originalRequest: Request,
        chain: Interceptor.Chain
    ): Response {
        val refreshToken = encryptedPreferences.getRefreshToken()
            ?: return createErrorResponse(chain.request(), 401, "No refresh token available")

        return try {
            val refreshResponse = authRepository.refreshToken(refreshToken)
            if (refreshResponse.isSuccessful) {
                refreshResponse.body()?.let { tokens ->
                    encryptedPreferences.saveAuthToken(tokens.accessToken)
                    encryptedPreferences.saveRefreshToken(tokens.refreshToken)
                }

                val retryRequest = originalRequest.newBuilder()
                    .header(AUTH_HEADER, "$BEARER_PREFIX${encryptedPreferences.getAuthToken()}")
                    .build()

                chain.proceed(retryRequest)
            } else {
                encryptedPreferences.clearAuthData()
                createErrorResponse(chain.request(), 401, "Token refresh failed")
            }
        } catch (e: Exception) {
            createErrorResponse(chain.request(), 401, "Token refresh error: ${e.message}")
        }
    }

    private fun createErrorResponse(request: Request, code: Int, message: String): Response {
        return Response.Builder()
            .request(request)
            .protocol(Protocol.HTTP_1_1)
            .code(code)
            .message(message)
            .body(
                "{\"error\":\"$message\"}".toResponseBody("application/json".toMediaTypeOrNull())
            )
            .build()
    }
}
```

## 4. Data Layer Implementation

### 4.1 Room Database Configuration

The Room database provides local persistence for queries, workflows, and user data with support for reactive queries using Flow. The database schema uses foreign key relationships to maintain referential integrity and cascade delete behavior for proper cleanup when associated entities are removed. Type converters handle complex types that Room cannot persist natively, including dates and JSON data.

```kotlin
@Entity(
    tableName = "queries",
    indices = [
        Index(value = ["queryId"], unique = true),
        Index(value = ["timestamp"]),
        Index(value = ["status"])
    ]
)
data class QueryEntity(
    @PrimaryKey
    @ColumnInfo(name = "query_id")
    val queryId: String,

    @ColumnInfo(name = "query_text")
    val queryText: String,

    @ColumnInfo(name = "response_text")
    val responseText: String? = null,

    @ColumnInfo(name = "model_used")
    val modelUsed: String? = null,

    @ColumnInfo(name = "complexity")
    val complexity: String,

    @ColumnInfo(name = "execution_mode")
    val executionMode: String,

    @ColumnInfo(name = "confidence")
    val confidence: Float,

    @ColumnInfo(name = "latency_ms")
    val latencyMs: Float,

    @ColumnInfo(name = "status")
    val status: String,

    @ColumnInfo(name = "feedback_type")
    val feedbackType: String? = null,

    @ColumnInfo(name = "timestamp")
    val timestamp: Long,

    @ColumnInfo(name = "sync_status")
    val syncStatus: Int = SyncStatus.SYNCED
)

@Entity(
    tableName = "workflows",
    indices = [
        Index(value = ["workflowId"], unique = true),
        Index(value = ["status"]),
        Index(value = ["timestamp"])
    ]
)
data class WorkflowEntity(
    @PrimaryKey
    @ColumnInfo(name = "workflow_id")
    val workflowId: String,

    @ColumnInfo(name = "name")
    val name: String,

    @ColumnInfo(name = "description")
    val description: String? = null,

    @ColumnInfo(name = "total_steps")
    val totalSteps: Int,

    @ColumnInfo(name = "completed_steps")
    val completedSteps: Int,

    @ColumnInfo(name = "status")
    val status: String,

    @ColumnInfo(name = "results")
    val results: String? = null,

    @ColumnInfo(name = "duration_ms")
    val durationMs: Float,

    @ColumnInfo(name = "timestamp")
    val timestamp: Long,

    @ColumnInfo(name = "sync_status")
    val syncStatus: Int = SyncStatus.SYNCED
)

@Entity(
    tableName = "users",
    indices = [Index(value = ["userId"], unique = true)]
)
data class UserEntity(
    @PrimaryKey
    @ColumnInfo(name = "user_id")
    val userId: String,

    @ColumnInfo(name = "email")
    val email: String,

    @ColumnInfo(name = "display_name")
    val displayName: String? = null,

    @ColumnInfo(name = "avatar_url")
    val avatarUrl: String? = null,

    @ColumnInfo(name = "preferences")
    val preferences: String? = null,

    @ColumnInfo(name = "last_active")
    val lastActive: Long
)

object SyncStatus {
    const val SYNCED = 0
    const val PENDING_UPLOAD = 1
    const val PENDING_DOWNLOAD = 2
    const val CONFLICT = 3
}

@Dao
interface QueryDao {

    @Query("SELECT * FROM queries ORDER BY timestamp DESC")
    fun getAllQueries(): Flow<List<QueryEntity>>

    @Query("SELECT * FROM queries WHERE status = :status ORDER BY timestamp DESC")
    fun getQueriesByStatus(status: String): Flow<List<QueryEntity>>

    @Query("SELECT * FROM queries WHERE query_id = :queryId")
    suspend fun getQueryById(queryId: String): QueryEntity?

    @Query("SELECT * FROM queries WHERE sync_status = :syncStatus")
    suspend fun getQueriesBySyncStatus(syncStatus: Int): List<QueryEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQuery(query: QueryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQueries(queries: List<QueryEntity>)

    @Update
    suspend fun updateQuery(query: QueryEntity)

    @Query("UPDATE queries SET sync_status = :syncStatus WHERE query_id = :queryId")
    suspend fun updateSyncStatus(queryId: String, syncStatus: Int)

    @Query("UPDATE queries SET feedback_type = :feedbackType WHERE query_id = :queryId")
    suspend fun updateFeedback(queryId: String, feedbackType: String)

    @Query("DELETE FROM queries WHERE query_id = :queryId")
    suspend fun deleteQuery(queryId: String)

    @Query("DELETE FROM queries WHERE timestamp < :timestamp")
    suspend fun deleteOldQueries(timestamp: Long)
}

@Dao
interface WorkflowDao {

    @Query("SELECT * FROM workflows ORDER BY timestamp DESC")
    fun getAllWorkflows(): Flow<List<WorkflowEntity>>

    @Query("SELECT * FROM workflows WHERE status = :status ORDER BY timestamp DESC")
    fun getWorkflowsByStatus(status: String): Flow<List<WorkflowEntity>>

    @Query("SELECT * FROM workflows WHERE workflow_id = :workflowId")
    suspend fun getWorkflowById(workflowId: String): WorkflowEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertWorkflow(workflow: WorkflowEntity)

    @Update
    suspend fun updateWorkflow(workflow: WorkflowEntity)

    @Query("UPDATE workflows SET status = :status, completed_steps = :completedSteps WHERE workflow_id = :workflowId")
    suspend fun updateWorkflowProgress(workflowId: String, status: String, completedSteps: Int)

    @Query("DELETE FROM workflows WHERE workflow_id = :workflowId")
    suspend fun deleteWorkflow(workflowId: String)
}

@Database(
    entities = [QueryEntity::class, WorkflowEntity::class, UserEntity::class],
    version = 1,
    exportSchema = true
)
abstract class AmaimaDatabase : RoomDatabase() {
    abstract fun queryDao(): QueryDao
    abstract fun workflowDao(): WorkflowDao
    abstract fun userDao(): UserDao
}
```

### 4.2 Repository Implementations

Repository implementations coordinate data from local and remote sources, implementing offline-first patterns where reads always serve cached data and writes are queued for background synchronization. The repository layer abstracts the data source details from the domain layer, enabling transparent switching between local and remote data without affecting use case implementations.

```kotlin
class QueryRepositoryImpl(
    private val api: AmaimaApi,
    private val queryDao: QueryDao,
    private val networkMonitor: NetworkMonitor
) : QueryRepository {

    private val _queries = MutableStateFlow<List<Query>>(emptyList())

    override fun getQueryHistory(): Flow<List<Query>> {
        return queryDao.getAllQueries().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override fun getQueryById(queryId: String): Flow<Query?> {
        return queryDao.getAllQueries().map { entities ->
            entities.find { it.queryId == queryId }?.toDomain()
        }
    }

    override suspend fun submitQuery(request: QueryRequest): Result<QueryResponse> {
        val queryEntity = QueryEntity(
            queryId = UUID.randomUUID().toString(),
            queryText = request.query,
            responseText = null,
            modelUsed = null,
            complexity = "MODERATE",
            executionMode = "HYBRID_LOCAL_FIRST",
            confidence = 0f,
            latencyMs = 0f,
            status = QueryStatus.SUBMITTED.name,
            timestamp = System.currentTimeMillis(),
            syncStatus = SyncStatus.PENDING_UPLOAD
        )

        queryDao.insertQuery(queryEntity)

        return try {
            if (networkMonitor.isOnline()) {
                val response = api.submitQuery(request.toDto())
                if (response.isSuccessful) {
                    response.body()?.let { dto ->
                        val updatedEntity = queryEntity.copy(
                            responseText = dto.responseText,
                            modelUsed = dto.modelUsed,
                            confidence = dto.confidence,
                            latencyMs = dto.latencyMs,
                            status = QueryStatus.COMPLETED.name,
                            syncStatus = SyncStatus.SYNCED
                        )
                        queryDao.updateQuery(updatedEntity)
                        Result.success(updatedEntity.toResponse().toDomain())
                    } ?: Result.failure(ApiException("Empty response body"))
                } else {
                    queryDao.updateSyncStatus(queryEntity.queryId, SyncStatus.CONFLICT)
                    Result.failure(ApiException("API error: ${response.code()}"))
                }
            } else {
                queryDao.updateSyncStatus(queryEntity.queryId, SyncStatus.PENDING_UPLOAD)
                Result.success(QueryResponse(
                    responseId = queryEntity.queryId,
                    responseText = "Query queued for processing",
                    modelUsed = "OFFLINE",
                    routingDecision = RoutingDecision(
                        executionMode = "QUEUED",
                        modelSize = "NANO_1B",
                        complexity = "MODERATE",
                        securityLevel = "STANDARD",
                        confidence = 0.5f,
                        estimatedLatencyMs = 0f,
                        estimatedCost = 0f,
                        fallbackChain = emptyList()
                    ),
                    confidence = 0.5f,
                    latencyMs = 0f,
                    timestamp = Instant.now().toString()
                ))
            }
        } catch (e: Exception) {
            queryDao.updateSyncStatus(queryEntity.queryId, SyncStatus.CONFLICT)
            Result.failure(e)
        }
    }

    override suspend fun submitFeedback(queryId: String, feedback: Feedback): Result<Unit> {
        val query = queryDao.getQueryById(queryId)
            ?: return Result.failure(IllegalArgumentException("Query not found"))

        queryDao.updateFeedback(queryId, feedback.type.name)

        return if (networkMonitor.isOnline()) {
            try {
                api.submitFeedback(FeedbackRequestDto(queryId, feedback.type.name, feedback.comment))
                Result.success(Unit)
            } catch (e: Exception) {
                Result.failure(e)
            }
        } else {
            Result.success(Unit)
        }
    }

    override suspend fun syncPendingQueries() {
        val pendingQueries = queryDao.getQueriesBySyncStatus(SyncStatus.PENDING_UPLOAD)
        
        for (query in pendingQueries) {
            try {
                val request = QueryRequestDto(
                    query = query.queryText,
                    operation = "general"
                )
                val response = api.submitQuery(request)
                if (response.isSuccessful) {
                    queryDao.updateSyncStatus(query.queryId, SyncStatus.SYNCED)
                }
            } catch (e: Exception) {
                Log.e("QueryRepository", "Sync failed for query ${query.queryId}", e)
            }
        }
    }

    override suspend fun clearOldQueries(olderThanDays: Int) {
        val cutoffTime = System.currentTimeMillis() - (olderThanDays * 24 * 60 * 60 * 1000L)
        queryDao.deleteOldQueries(cutoffTime)
    }

    private fun QueryEntity.toDomain(): Query {
        return Query(
            id = queryId,
            text = queryText,
            response = responseText,
            modelUsed = modelUsed,
            complexity = complexity,
            executionMode = executionMode,
            confidence = confidence,
            status = QueryStatus.valueOf(status),
            timestamp = Instant.ofEpochMilli(timestamp)
        )
    }

    private fun QueryRequest.toDto(): QueryRequestDto {
        return QueryRequestDto(
            query = query,
            operation = operation,
            fileTypes = fileTypes,
            userId = userId,
            preferences = preferences
        )
    }

    private fun QueryEntity.toResponse(): QueryResponseDto {
        return QueryResponseDto(
            responseId = queryId,
            responseText = responseText ?: "",
            modelUsed = modelUsed ?: "UNKNOWN",
            routingDecision = RoutingDecisionDto(
                executionMode = executionMode,
                modelSize = "MEDIUM_7B",
                complexity = complexity,
                securityLevel = "STANDARD",
                confidence = confidence,
                estimatedLatencyMs = latencyMs,
                estimatedCost = 0f,
                fallbackChain = emptyList()
            ),
            confidence = confidence,
            latencyMs = latencyMs,
            timestamp = Instant.ofEpochMilli(timestamp).toString()
        )
    }
}
```

## 5. Presentation Layer Implementation

### 5.1 Navigation Setup

The navigation component manages screen transitions with type-safe arguments and deep link handling. The navigation graph defines all reachable destinations with their associated arguments, animations, and required permissions. Bottom navigation provides access to the primary feature areas with badges indicating pending items or notifications.

```kotlin
sealed class Screen(val route: String) {
    data object Home : Screen("home")
    data object Query : Screen("query")
    data object QueryDetail : Screen("query/{queryId}") {
        fun createRoute(queryId: String) = "query/$queryId"
    }
    data object Workflow : Screen("workflow")
    data object WorkflowDetail : Screen("workflow/{workflowId}") {
        fun createRoute(workflowId: String) = "workflow/$workflowId"
    }
    data object Models : Screen("models")
    data object Settings : Screen("settings")
    data object Login : Screen("login")
    data object Register : Screen("register")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AmaimaNavHost(
    navController: NavHostController,
    startDestination: String = Screen.Home.route,
    onDeepLink: (String) -> Unit = {}
) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val bottomNavItems = listOf(
        Triple(Screen.Home, "Home", Icons.Filled.Home),
        Triple(Screen.Query, "Query", Icons.Filled.Edit),
        Triple(Screen.Workflow, "Workflow", Icons.Filled.AccountTree),
        Triple(Screen.Models, "Models", Icons.Filled.Memory)
    )

    val showBottomBar = currentRoute in bottomNavItems.map { it.first.route }

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    bottomNavItems.forEach { (screen, label, icon) ->
                        NavigationBarItem(
                            icon = { Icon(icon, contentDescription = label) },
                            label = { Text(label) },
                            selected = currentRoute == screen.route,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(Screen.Home.route) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            }
                        )
                    }
                }
            }
        }
    ) { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = startDestination,
            modifier = Modifier.padding(paddingValues)
        ) {
            composable(Screen.Home.route) {
                val viewModel: HomeViewModel = hiltViewModel()
                val state by viewModel.state.collectAsState()
                val networkMonitor = NetworkMonitor.getInstance()

                HomeScreen(
                    state = state,
                    onQueryClick = { navController.navigate(Screen.Query.route) },
                    onWorkflowClick = { navController.navigate(Screen.Workflow.route) },
                    onQueryHistoryItemClick = { queryId ->
                        navController.navigate(Screen.QueryDetail.createRoute(queryId))
                    },
                    onSettingsClick = { navController.navigate(Screen.Settings.route) },
                    isOnline = networkMonitor.isOnline()
                )
            }

            composable(Screen.Query.route) {
                val viewModel: QueryViewModel = hiltViewModel()
                val state by viewModel.state.collectAsState()

                QueryScreen(
                    state = state,
                    onQueryChange = viewModel::onQueryChange,
                    onSubmitQuery = viewModel::submitQuery,
                    onProvideFeedback = viewModel::provideFeedback,
                    onClearQuery = viewModel::clearQuery,
                    onBackClick = { navController.popBackStack() }
                )
            }

            composable(
                route = Screen.QueryDetail.route,
                arguments = listOf(
                    navArgument("queryId") { type = NavType.StringType }
                )
            ) { backStackEntry ->
                val queryId = backStackEntry.arguments?.getString("queryId") ?: ""
                val viewModel: QueryDetailViewModel = hiltViewModel()
                val state by viewModel.state.collectAsState()

                QueryDetailScreen(
                    queryId = queryId,
                    state = state,
                    onBackClick = { navController.popBackStack() }
                )
            }

            composable(Screen.Workflow.route) {
                val viewModel: WorkflowViewModel = hiltViewModel()
                val state by viewModel.state.collectAsState()

                WorkflowScreen(
                    state = state,
                    onCreateWorkflow = viewModel::createWorkflow,
                    onWorkflowClick = { workflowId ->
                        navController.navigate(Screen.WorkflowDetail.createRoute(workflowId))
                    },
                    onRefresh = viewModel::refreshWorkflows
                )
            }

            composable(Screen.Settings.route) {
                SettingsScreen(
                    onLogout = { /* Handle logout */ },
                    onClearCache = { /* Handle cache clear */ },
                    onThemeChange = { /* Handle theme change */ }
                )
            }
        }
    }
}
```

### 5.2 Home Screen Implementation

The Home screen serves as the primary entry point, displaying system status, recent activity, and quick actions. The design uses cards to group related information with Material 3 elevation and color theming. Real-time status indicators show connection state and backend health through the WebSocket connection.

```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    state: HomeState,
    onQueryClick: () -> Unit,
    onWorkflowClick: () -> Unit,
    onQueryHistoryItemClick: (String) -> Unit,
    onSettingsClick: () -> Unit,
    isOnline: Boolean
) {
    val context = LocalContext.current

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "AMAIMA",
                            style = MaterialTheme.typography.headlineMedium
                        )
                        Text(
                            text = if (isOnline) "Connected" else "Offline Mode",
                            style = MaterialTheme.typography.bodySmall,
                            color = if (isOnline) {
                                MaterialTheme.colorScheme.primary
                            } else {
                                MaterialTheme.colorScheme.error
                            }
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { /* Notifications */ }) {
                        BadgedBox(
                            badge = {
                                if (state.pendingFeedbackCount > 0) {
                                    Badge { Text(state.pendingFeedbackCount.toString()) }
                                }
                            }
                        ) {
                            Icon(Icons.Default.Notifications, contentDescription = "Notifications")
                        }
                    }
                    IconButton(onClick = onSettingsClick) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .pullToRefresh(
                    isRefreshing = state.isRefreshing,
                    onRefresh = { /* Handle refresh */ }
                ),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                SystemStatusCard(
                    systemStats = state.systemStats,
                    isLoading = state.isLoading
                )
            }

            item {
                QuickActionsRow(
                    onNewQuery = onQueryClick,
                    onNewWorkflow = onWorkflowClick
                )
            }

            item {
                Text(
                    text = "Recent Queries",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(top = 8.dp)
                )
            }

            if (state.recentQueries.isEmpty()) {
                item {
                    EmptyStateCard(
                        message = "No recent queries",
                        actionLabel = "Start Query",
                        onAction = onQueryClick
                    )
                }
            } else {
                items(state.recentQueries.take(5)) { query ->
                    QueryHistoryCard(
                        query = query,
                        onClick = { onQueryHistoryItemClick(query.id) }
                    )
                }
            }

            item {
                Text(
                    text = "Active Workflows",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(top = 8.dp)
                )
            }

            items(state.activeWorkflows.take(3)) { workflow ->
                WorkflowStatusCard(
                    workflow = workflow,
                    onClick = { /* Navigate to detail */ }
                )
            }
        }
    }
}

@Composable
fun SystemStatusCard(
    systemStats: SystemStats?,
    isLoading: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        if (isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = "System Status",
                    style = MaterialTheme.typography.titleMedium
                )
                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    StatusItem(
                        label = "Uptime",
                        value = systemStats?.uptime ?: "Unknown"
                    )
                    StatusItem(
                        label = "Active Models",
                        value = systemStats?.activeModels?.toString() ?: "0"
                    )
                    StatusItem(
                        label = "Queries/Min",
                        value = systemStats?.queriesPerMinute?.toString() ?: "0"
                    )
                    StatusItem(
                        label = "Health",
                        value = systemStats?.health ?: "Unknown",
                        valueColor = when (systemStats?.health) {
                            "healthy" -> MaterialTheme.colorScheme.primary
                            "degraded" -> MaterialTheme.colorScheme.error
                            else -> MaterialTheme.colorScheme.onSurface
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun StatusItem(
    label: String,
    value: String,
    valueColor: Color = MaterialTheme.colorScheme.onSurface
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = value,
            style = MaterialTheme.typography.headlineSmall,
            color = valueColor
        )
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun QuickActionsRow(
    onNewQuery: () -> Unit,
    onNewWorkflow: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        QuickActionButton(
            modifier = Modifier.weight(1f),
            icon = Icons.Default.Edit,
            label = "New Query",
            onClick = onNewQuery
        )
        QuickActionButton(
            modifier = Modifier.weight(1f),
            icon = Icons.Default.AccountTree,
            label = "New Workflow",
            onClick = onNewWorkflow
        )
    }
}

@Composable
fun QuickActionButton(
    modifier: Modifier = Modifier,
    icon: ImageVector,
    label: String,
    onClick: () -> Unit
) {
    Card(
        modifier = modifier,
        onClick = onClick,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(32.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge
            )
        }
    }
}

@Composable
fun QueryHistoryCard(
    query: Query,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        onClick = onClick
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = query.text.take(50),
                    style = MaterialTheme.typography.bodyMedium,
                    maxLines = 2
                )
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    AssistChip(
                        onClick = { },
                        label = { Text(query.complexity, style = MaterialTheme.typography.labelSmall) }
                    )
                    Text(
                        text = "${query.latencyMs.toInt()}ms",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            Icon(
                imageVector = Icons.Default.ChevronRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
```

### 5.3 Query Screen Implementation

The Query screen provides the primary interface for submitting queries to the AMAIMA backend. The design includes a text input area with character count, operation type selection, and file attachment support. Real-time feedback during query processing shows progress through animated indicators and streaming response display when available.

```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QueryScreen(
    state: QueryState,
    onQueryChange: (String) -> Unit,
    onSubmitQuery: () -> Unit,
    onProvideFeedback: (Feedback) -> Unit,
    onClearQuery: () -> Unit,
    onBackClick: () -> Unit
) {
    val scrollState = rememberScrollState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("New Query") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (state.query.isNotEmpty()) {
                        IconButton(onClick = onClearQuery) {
                            Icon(Icons.Default.Clear, contentDescription = "Clear")
                        }
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .padding(16.dp)
                    .verticalScroll(scrollState)
            ) {
                OutlinedTextField(
                    value = state.query,
                    onValueChange = onQueryChange,
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 150.dp),
                    placeholder = { Text("Enter your query...") },
                    supportingText = {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("${state.query.length} / 10000")
                            Text(state.currentComplexity)
                        }
                    },
                    enabled = state.status != QueryStatus.PROCESSING,
                    maxLines = 10
                )

                Spacer(modifier = Modifier.height(16.dp))

                OperationTypeSelector(
                    selectedType = state.selectedOperation,
                    onTypeSelected = { /* Handle operation type selection */ }
                )

                Spacer(modifier = Modifier.height(16.dp))

                FileAttachmentSection(
                    attachedFiles = state.attachedFiles,
                    onAttachFile = { /* Handle file attachment */ },
                    onRemoveFile = { /* Handle file removal */ }
                )

                if (state.status == QueryStatus.ERROR) {
                    Spacer(modifier = Modifier.height(16.dp))
                    ErrorCard(
                        message = state.errorMessage ?: "An error occurred",
                        onRetry = onSubmitQuery
                    )
                }
            }

            QuerySubmissionBar(
                status = state.status,
                canSubmit = state.query.isNotBlank() && state.status != QueryStatus.PROCESSING,
                onSubmit = onSubmitQuery
            )

            if (state.status == QueryStatus.COMPLETED && state.response != null) {
                ResponseCard(
                    response = state.response,
                    onProvideFeedback = onProvideFeedback
                )
            }
        }
    }
}

@Composable
fun OperationTypeSelector(
    selectedType: String,
    onTypeSelected: (String) -> Unit
) {
    val operationTypes = listOf(
        "general" to "General",
        "code" to "Code Generation",
        "analysis" to "Analysis",
        "creative" to "Creative",
        "qa" to "Question Answering"
    )

    LazyRow(
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(operationTypes) { (value, label) ->
            FilterChip(
                selected = selectedType == value,
                onClick = { onTypeSelected(value) },
                label = { Text(label) }
            )
        }
    }
}

@Composable
fun FileAttachmentSection(
    attachedFiles: List<AttachedFile>,
    onAttachFile: () -> Unit,
    onRemoveFile: (AttachedFile) -> Unit
) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Attachments",
                style = MaterialTheme.typography.titleSmall
            )
            TextButton(onClick = onAttachFile) {
                Icon(Icons.Default.AttachFile, contentDescription = null)
                Spacer(modifier = Modifier.width(4.dp))
                Text("Add File")
            }
        }

        if (attachedFiles.isNotEmpty()) {
            Spacer(modifier = Modifier.height(8.dp))
            attachedFiles.forEach { file ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = when (file.mimeType) {
                            "image/*" -> Icons.Default.Image
                            "text/*" -> Icons.Default.Description
                            else -> Icons.Default.InsertDriveFile
                        },
                        contentDescription = null,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = file.name,
                        modifier = Modifier.weight(1f),
                        style = MaterialTheme.typography.bodySmall
                    )
                    IconButton(
                        onClick = { onRemoveFile(file) },
                        modifier = Modifier.size(24.dp)
                    ) {
                        Icon(
                            Icons.Default.Close,
                            contentDescription = "Remove",
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ResponseCard(
    response: QueryResponse,
    onProvideFeedback: (Feedback) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Response",
                    style = MaterialTheme.typography.titleMedium
                )
                ConfidenceBadge(confidence = response.confidence)
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = response.responseText,
                style = MaterialTheme.typography.bodyMedium
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Model: ${response.modelUsed}",
                        style = MaterialTheme.typography.labelSmall
                    )
                    Text(
                        text = "Latency: ${response.latencyMs.toInt()}ms",
                        style = MaterialTheme.typography.labelSmall
                    )
                }

                FeedbackButtons(
                    onPositiveFeedback = {
                        onProvideFeedback(Feedback(FeedbackType.THUMBS_UP))
                    },
                    onNegativeFeedback = {
                        onProvideFeedback(Feedback(FeedbackType.THUMBS_DOWN))
                    }
                )
            }
        }
    }
}

@Composable
fun ConfidenceBadge(confidence: Float) {
    val (color, label) = when {
        confidence >= 0.9f -> MaterialTheme.colorScheme.primary to "High"
        confidence >= 0.7f -> MaterialTheme.colorScheme.tertiary to "Medium"
        else -> MaterialTheme.colorScheme.error to "Low"
    }

    Surface(
        color = color.copy(alpha = 0.1f),
        shape = MaterialTheme.shapes.small
    ) {
        Text(
            text = "$label (${(confidence * 100).toInt()}%)",
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelSmall,
            color = color
        )
    }
}

@Composable
fun FeedbackButtons(
    onPositiveFeedback: () -> Unit,
    onNegativeFeedback: () -> Unit
) {
    Row {
        IconButton(onClick = onPositiveFeedback) {
            Icon(
                Icons.Default.ThumbUp,
                contentDescription = "Positive feedback",
                tint = MaterialTheme.colorScheme.primary
            )
        }
        IconButton(onClick = onNegativeFeedback) {
            Icon(
                Icons.Default.ThumbDown,
                contentDescription = "Negative feedback",
                tint = MaterialTheme.colorScheme.error
            )
        }
    }
}

@Composable
fun QuerySubmissionBar(
    status: QueryStatus,
    canSubmit: Boolean,
    onSubmit: () -> Unit
) {
    Surface(
        tonalElevation = 3.dp,
        shadowElevation = 8.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            when (status) {
                QueryStatus.IDLE -> {
                    Text(
                        text = "Ready to submit",
                        style = MaterialTheme.typography.bodySmall
                    )
                    Button(
                        onClick = onSubmit,
                        enabled = canSubmit
                    ) {
                        Icon(Icons.Default.Send, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Submit")
                    }
                }
                QueryStatus.PROCESSING -> {
                    LinearProgressIndicator(
                        modifier = Modifier
                            .weight(1f)
                            .padding(end = 16.dp)
                    )
                    Text(
                        text = "Processing...",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                QueryStatus.COMPLETED -> {
                    Text(
                        text = "Query complete",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                    OutlinedButton(onClick = onSubmit) {
                        Text("Submit New")
                    }
                }
                QueryStatus.ERROR -> {
                    Text(
                        text = "Error occurred",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error
                    )
                    Button(onClick = onSubmit) {
                        Text("Retry")
                    }
                }
            }
        }
    }
}
```

## 6. Machine Learning Integration

### 6.1 TensorFlow Lite Manager

The TensorFlow Lite Manager handles on-device machine learning capabilities, loading models asynchronously and managing their lifecycle. The manager implements a download queue for retrieving models on demand, caching strategies to minimize storage usage, and version checking to ensure models are current with backend expectations.

```kotlin
class TensorFlowLiteManager(
    private val context: Context,
    private val modelDownloader: ModelDownloader
) {
    private val models = ConcurrentHashMap<String, TensorFlowLiteModel>()
    private val interpreterMap = ConcurrentHashMap<String, Interpreter>()

    companion object {
        private const val MODEL_CACHE_SIZE = 500L * 1024 * 1024 // 500MB
        private const val MODEL_VERSION = "1.0.0"
    }

    data class TensorFlowLiteModel(
        val name: String,
        val version: String,
        val modelPath: String,
        val inputShape: IntArray,
        val outputShape: IntArray,
        val labels: List<String>
    ) {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            other as TensorFlowLiteModel
            return name == other.name && version == other.version
        }

        override fun hashCode(): Int {
            var result = name.hashCode()
            result = 31 * result + version.hashCode()
            return result
        }
    }

    suspend fun loadDefaultModels() {
        val defaultModels = listOf(
            TensorFlowLiteModel(
                name = "complexity_estimator",
                version = MODEL_VERSION,
                modelPath = "models/complexity_estimator.tflite",
                inputShape = intArrayOf(1, 128),
                outputShape = intArrayOf(1, 5),
                labels = listOf("TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "EXPERT")
            ),
            TensorFlowLiteModel(
                name = "keyword_extractor",
                version = MODEL_VERSION,
                modelPath = "models/keyword_extractor.tflite",
                inputShape = intArrayOf(1, 64),
                outputShape = intArrayOf(1, 10),
                labels = emptyList()
            ),
            TensorFlowLiteModel(
                name = "sentiment_analyzer",
                version = MODEL_VERSION,
                modelPath = "models/sentiment_analyzer.tflite",
                inputShape = intArrayOf(1, 128),
                outputShape = intArrayOf(1, 3),
                labels = listOf("NEGATIVE", "NEUTRAL", "POSITIVE")
            )
        )

        defaultModels.forEach { model ->
            loadModel(model)
        }
    }

    suspend fun loadModel(model: TensorFlowLiteModel) {
        withContext(Dispatchers.IO) {
            try {
                val modelFile = File(context.filesDir, model.modelPath)
                
                if (!modelFile.exists()) {
                    val downloaded = modelDownloader.downloadModel(model.name, modelFile)
                    if (!downloaded) {
                        Log.w(TAG, "Failed to download model: ${model.name}")
                        return@withContext
                    }
                }

                val options = Interpreter.Options().apply {
                    setNumThreads(4)
                }

                val interpreter = Interpreter(modelFile, options)
                interpreterMap[model.name] = interpreter
                models[model.name] = model
                
                Log.d(TAG, "Model loaded: ${model.name}")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to load model: ${model.name}", e)
            }
        }
    }

    fun estimateComplexity(query: String): ComplexityResult {
        val interpreter = interpreterMap["complexity_estimator"]
            ?: return ComplexityResult(
                complexity = "MODERATE",
                confidence = 0.5f,
                method = "default"
            )

        return try {
            val input = preprocessQuery(query)
            val output = Array(1) { FloatArray(5) }
            interpreter.run(input, output)

            val probabilities = output[0]
            val maxIndex = probabilities.indices.maxByOrNull { probabilities[it] } ?: 2

            val complexity = when (maxIndex) {
                0 -> "TRIVIAL"
                1 -> "SIMPLE"
                2 -> "MODERATE"
                3 -> "COMPLEX"
                4 -> "EXPERT"
                else -> "MODERATE"
            }

            ComplexityResult(
                complexity = complexity,
                confidence = probabilities[maxIndex],
                method = "ml_model"
            )
        } catch (e: Exception) {
            Log.e(TAG, "Complexity estimation failed", e)
            ComplexityResult("MODERATE", 0.5f, "fallback")
        }
    }

    fun analyzeSentiment(text: String): SentimentResult {
        val interpreter = interpreterMap["sentiment_analyzer"]
            ?: return SentimentResult("NEUTRAL", 0.5f)

        return try {
            val input = preprocessText(text)
            val output = Array(1) { FloatArray(3) }
            interpreter.run(input, output)

            val probabilities = output[0]
            val maxIndex = probabilities.indices.maxByOrNull { probabilities[it] } ?: 1

            val sentiment = when (maxIndex) {
                0 -> "NEGATIVE"
                1 -> "NEUTRAL"
                2 -> "POSITIVE"
                else -> "NEUTRAL"
            }

            SentimentResult(sentiment, probabilities[maxIndex])
        } catch (e: Exception) {
            Log.e(TAG, "Sentiment analysis failed", e)
            SentimentResult("NEUTRAL", 0.5f)
        }
    }

    private fun preprocessQuery(query: String): Array<FloatArray> {
        val tokens = query.lowercase()
            .replace(Regex("[^a-z0-9\\s]"), "")
            .split("\\s+")
            .take(128)

        val vector = FloatArray(128) { 0f }
        tokens.forEachIndexed { index, token ->
            vector[index] = token.hashCode().toFloat() / Float.MAX_VALUE
        }

        return arrayOf(vector)
    }

    private fun preprocessText(text: String): Array<FloatArray> {
        return preprocessQuery(text)
    }

    fun getLoadedModels(): List<String> {
        return models.keys.toList()
    }

    fun isModelLoaded(modelName: String): Boolean {
        return interpreterMap.containsKey(modelName)
    }

    suspend fun unloadModel(modelName: String) {
        withContext(Dispatchers.IO) {
            interpreterMap.remove(modelName)?.close()
            models.remove(modelName)
            Log.d(TAG, "Model unloaded: $modelName")
        }
    }

    fun clearAllModels() {
        interpreterMap.values.forEach { it.close() }
        interpreterMap.clear()
        models.clear()
    }

    data class ComplexityResult(
        val complexity: String,
        val confidence: Float,
        val method: String
    )

    data class SentimentResult(
        val sentiment: String,
        val confidence: Float
    )
}
```

## 7. Security Implementation

### 7.1 Biometric Authentication

Biometric authentication provides secure, convenient device-level access control for the application. The implementation supports fingerprint, face recognition, and device credential fallback, with clear user guidance throughout the authentication flow. Successful authentication grants access to sensitive features and retrieves encrypted API tokens from secure storage.

```kotlin
class BiometricAuthManager(
    private val context: Context
) {
    private val biometricPrompt: BiometricPrompt
    private val promptInfo: BiometricPrompt.PromptInfo

    private val _authenticationState = MutableStateFlow(AuthenticationState.IDLE)
    val authenticationState: StateFlow<AuthenticationState> = _authenticationState.asStateFlow()

    sealed class AuthenticationState {
        data object IDLE : AuthenticationState()
        data object AUTHENTICATING : AuthenticationState()
        data object SUCCESS : AuthenticationState()
        data object FAILED : AuthenticationState()
        data object ERROR : AuthenticationState()
        data object CANCELLED : AuthenticationState()
    }

    init {
        val executor = ContextCompat.getMainExecutor(context)

        biometricPrompt = BiometricPrompt(
            context as Activity,
            executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    _authenticationState.value = AuthenticationState.SUCCESS
                    handleAuthenticationSuccess(result)
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    when (errorCode) {
                        BiometricPrompt.ERROR_CANCELED,
                        BiometricPrompt.ERROR_USER_CANCELED,
                        BiometricPrompt.ERROR_NEGATIVE_BUTTON -> {
                            _authenticationState.value = AuthenticationState.CANCELLED
                        }
                        else -> {
                            _authenticationState.value = AuthenticationState.ERROR
                        }
                    }
                }

                override fun onAuthenticationFailed() {
                    _authenticationState.value = AuthenticationState.FAILED
                }
            }
        )

        promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Authenticate to AMAIMA")
            .setSubtitle("Use biometrics to access secure features")
            .setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_STRONG or
                BiometricManager.Authenticators.BIOMETRIC_WEAK
            )
            .build()
    }

    fun canAuthenticate(): BiometricCapability {
        val biometricManager = BiometricManager.from(context)
        return when (biometricManager.canAuthenticate(
            BiometricManager.Authenticators.BIOMETRIC_STRONG or
            BiometricManager.Authenticators.BIOMETRIC_WEAK
        )) {
            BiometricManager.BIOMETRIC_SUCCESS -> BiometricCapability.AVAILABLE
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> BiometricCapability.NO_HARDWARE
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE -> BiometricCapability.HARDWARE_UNAVAILABLE
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> BiometricCapability.NOT_ENROLLED
            else -> BiometricCapability.UNAVAILABLE
        }
    }

    fun authenticate(purpose: AuthenticationPurpose = AuthenticationPurpose.GENERAL) {
        val updatedPromptInfo = promptInfo.toBuilder()
            .setTitle(getPromptTitle(purpose))
            .setSubtitle(getPromptSubtitle(purpose))
            .build()

        _authenticationState.value = AuthenticationState.AUTHENTICATING
        biometricPrompt.authenticate(updatedPromptInfo)
    }

    private fun handleAuthenticationSuccess(result: BiometricPrompt.AuthenticationResult) {
        val cryptoObject = result.cryptoObject
        if (cryptoObject != null) {
            useCryptoObject(cryptoObject, purpose)
        }
    }

    private fun useCryptoObject(cryptoObject: BiometricPrompt.CryptoObject, purpose: AuthenticationPurpose) {
        when (purpose) {
            AuthenticationPurpose.UNLOCK_SECURE_DATA -> {
                val encryptedPrefs = EncryptedPreferences.getInstance()
                encryptedPrefs.setAuthenticated(true)
            }
            AuthenticationPurpose.SIGN_TRANSACTION -> {
                // Handle transaction signing
            }
            else -> {
                val encryptedPrefs = EncryptedPreferences.getInstance()
                encryptedPrefs.setAuthenticated(true)
            }
        }
    }

    private fun getPromptTitle(purpose: AuthenticationPurpose): String {
        return when (purpose) {
            AuthenticationPurpose.GENERAL -> "Authenticate to AMAIMA"
            AuthenticationPurpose.UNLOCK_SECURE_DATA -> "Unlock Secure Data"
            AuthenticationPurpose.SIGN_TRANSACTION -> "Confirm Transaction"
            AuthenticationPurpose.ENABLE_BIOMETRIC -> "Enable Biometric Login"
        }
    }

    private fun getPromptSubtitle(purpose: AuthenticationPurpose): String {
        return when (purpose) {
            AuthenticationPurpose.GENERAL -> "Use biometrics to access your account"
            AuthenticationPurpose.UNLOCK_SECURE_DATA -> "Enter your credentials to continue"
            AuthenticationPurpose.SIGN_TRANSACTION -> "Confirm this transaction with biometrics"
            AuthenticationPurpose.ENROLL_BIOMETRIC -> "Set up biometric authentication"
        }
    }

    fun resetState() {
        _authenticationState.value = AuthenticationState.IDLE
    }

    enum class BiometricCapability {
        AVAILABLE,
        NO_HARDWARE,
        HARDWARE_UNAVAILABLE,
        NOT_ENROLLED,
        UNAVAILABLE
    }

    enum class AuthenticationPurpose {
        GENERAL,
        UNLOCK_SECURE_DATA,
        SIGN_TRANSACTION,
        ENABLE_BIOMETRIC
    }
}
```

### 7.2 Encrypted Preferences

Encrypted preferences provide secure storage for sensitive data including authentication tokens, user credentials, and application secrets. The implementation uses Android's EncryptedSharedPreferences, which automatically encrypts both keys and values using AES-256 encryption with hardware-backed key storage where available.

```kotlin
class EncryptedPreferences private constructor(
    private val context: Context
) {
    private val masterKey: MasterKey by lazy {
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .setKeyGenParameterSpec(
                KeyGenParameterSpec.Builder(
                    MasterKey.DEFAULT_MASTER_KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
                )
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setKeySize(256)
                    .build()
            )
            .build()
    }

    private val encryptedPrefs: SharedPreferences by lazy {
        EncryptedSharedPreferences.create(
            context,
            PREFS_FILE_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun getAuthToken(): String? {
        return encryptedPrefs.getString(KEY_AUTH_TOKEN, null)
    }

    fun saveAuthToken(token: String) {
        encryptedPrefs.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }

    fun getRefreshToken(): String? {
        return encryptedPrefs.getString(KEY_REFRESH_TOKEN, null)
    }

    fun saveRefreshToken(token: String) {
        encryptedPrefs.edit().putString(KEY_REFRESH_TOKEN, token).apply()
    }

    fun isAuthenticated(): Boolean {
        return encryptedPrefs.getBoolean(KEY_IS_AUTHENTICATED, false)
    }

    fun setAuthenticated(authenticated: Boolean) {
        encryptedPrefs.edit().putBoolean(KEY_IS_AUTHENTICATED, authenticated).apply()
    }

    fun getUserId(): String? {
        return encryptedPrefs.getString(KEY_USER_ID, null)
    }

    fun saveUserId(userId: String) {
        encryptedPrefs.edit().putString(KEY_USER_ID, userId).apply()
    }

    fun getApiKey(): String? {
        return encryptedPrefs.getString(KEY_API_KEY, null)
    }

    fun saveApiKey(apiKey: String) {
        encryptedPrefs.edit().putString(KEY_API_KEY, apiKey).apply()
    }

    fun clearAuthData() {
        val editor = encryptedPrefs.edit()
        editor.remove(KEY_AUTH_TOKEN)
        editor.remove(KEY_REFRESH_TOKEN)
        editor.remove(KEY_USER_ID)
        editor.remove(KEY_API_KEY)
        editor.putBoolean(KEY_IS_AUTHENTICATED, false)
        editor.apply()
    }

    fun clearAll() {
        encryptedPrefs.edit().clear().apply()
    }

    companion object {
        private const val PREFS_FILE_NAME = "amaima_secure_prefs"
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_API_KEY = "api_key"
        private const val KEY_IS_AUTHENTICATED = "is_authenticated"

        @Volatile
        private var instance: EncryptedPreferences? = null

        fun getInstance(context: Context): EncryptedPreferences {
            return instance ?: synchronized(this) {
                instance ?: EncryptedPreferences(
                    context.applicationContext
                ).also { instance = it }
            }
        }
    }
}
```

## 8. Build Configuration

### 8.1 Gradle Configuration

```kotlin
// settings.gradle.kts
pluginManagement {
    repositories {
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
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

// build.gradle.kts (Project level)
plugins {
    id("com.android.application") version "8.2.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.20" apply false
    id("com.google.dagger.hilt.android") version "2.48.1" apply false
    id("com.google.devtools.ksp") version "1.9.20-1.0.14" apply false
}

// build.gradle.kts (App level)
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.dagger.hilt.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "com.amaima.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.amaima.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "5.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        vectorDrawables {
            useSupportLibrary = true
        }

        buildConfigField("String", "API_BASE_URL", "\"https://api.amaima.example.com/\"")
        buildConfigField("String", "WS_BASE_URL", "\"wss://api.amaima.example.com\"")
        buildConfigField("Boolean", "ENABLE_LOGGING", "true")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.5"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }

    lint {
        abortOnError = false
        warningsAsErrors = false
        checkDependencies = true
    }

    testOptions {
        unitTests {
            isIncludeAndroidResources = true
        }
    }
}

dependencies {
    // Core Android
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
    implementation("androidx.activity:activity-compose:1.8.1")

    // Compose
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.7.5")

    // Lifecycle
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.6.2")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.6.2")

    // Hilt
    implementation("com.google.dagger:hilt-android:2.48.1")
    ksp("com.google.dagger:hilt-compiler:2.48.1")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")

    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.0")
    implementation("com.squareup.moshi:moshi-kotlin-codegen:1.15.0")

    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    // TensorFlow Lite
    implementation("org.tensorflow:tensorflow-lite:2.14.0")
    implementation("org.tensorflow:tensorflow-lite-support:0.4.4")

    // Biometric
    implementation("androidx.biometric:biometric:1.1.0")

    // Security
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")

    // DataStore
    implementation("androidx.datastore:datastore-preferences:1.0.0")

    // WorkManager
    implementation("androidx.work:work-runtime-ktx:2.9.0")
    implementation("androidx.hilt:hilt-work:1.1.0")
    ksp("androidx.hilt:hilt-compiler:1.1.0")

    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("app.cash.turbine:turbine:1.0.0")
    testImplementation("androidx.arch.core:core-testing:2.2.0")

    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2023.10.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
```

### 8.2 Android Manifest

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:name=".AmaimaApplication"
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="@xml/backup_rules"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.Amaima"
        android:networkSecurityConfig="@xml/network_security_config"
        tools:targetApi="34">

        <activity
            android:name=".presentation.MainActivity"
            android:exported="true"
            android:label="@string/app_name"
            android:theme="@style/Theme.Amaima"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data
                    android:scheme="amaima"
                    android:host="query" />
            </intent-filter>
        </activity>

        <service
            android:name=".data.sync.SyncService"
            android:exported="false"
            android:foregroundServiceType="dataSync" />

        <provider
            android:name="androidx.startup.InitializationProvider"
            android:authorities="${applicationId}.androidx-startup"
            android:exported="false"
            tools:node="merge">
            <meta-data
                android:name="androidx.work.WorkManagerInitializer"
                android:value="androidx.startup"
                tools:node="remove" />
        </provider>

    </application>

</manifest>
```

## 9. Summary and Conclusion

The AMAIMA Android client design presents a comprehensive, production-ready mobile application architecture that enables secure, efficient access to the Advanced Multimodal AI Model Architecture from Android devices. The implementation leverages modern Android development practices including Kotlin, Jetpack Compose, and Clean Architecture to deliver a maintainable, testable, and scalable codebase.

The architecture prioritizes user experience through real-time WebSocket communication, offline-first data handling, and progressive loading indicators. Security considerations are integrated at every layer, from encrypted storage for authentication tokens to biometric authentication for sensitive operations. The on-device TensorFlow Lite capabilities enable preprocessing and complexity estimation even when network connectivity is unavailable, providing value beyond simple API proxying.

The modular package structure facilitates parallel development and enables future expansion with new features without requiring changes to the core architecture. The dependency injection setup provides clear boundaries between components, enabling thorough unit testing and facilitating build variant configurations for different deployment environments.

The APK design specification provides sufficient detail for implementation teams to begin development immediately, with clear API contracts, database schemas, and UI component specifications. The Gradle build configuration ensures consistent builds across development machines while optimizing release builds for distribution through the Google Play Store or enterprise distribution channels.
