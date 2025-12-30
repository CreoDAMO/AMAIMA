// mobile/data/websocket/WebSocketManager.kt

class WebSocketManager(
    private val okHttpClient: OkHttpClient,
    private val encryptedPrefs: EncryptedPreferences
) {
    private var webSocket: WebSocket? = null
    private var reconnectAttempts = 0
    private val maxReconnectAttempts = 5
    private val baseReconnectDelay = 1000L
    private var isManualDisconnect = false
    private var heartbeatJob: Job? = null

    private val _messageFlow = MutableSharedFlow<WebSocketMessage>(
        replay = 0,
        extraBufferCapacity = 64
    )
    val messageFlow: SharedFlow<WebSocketMessage> = _messageFlow.asSharedFlow()

    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    sealed class ConnectionState {
        object CONNECTING : ConnectionState()
        object CONNECTED : ConnectionState()
        object DISCONNECTED : ConnectionState()
        data class ERROR(val message: String) : ConnectionState()
    }

    sealed class WebSocketMessage {
        data class QueryUpdate(val data: QueryUpdateData) : WebSocketMessage()
        data class WorkflowUpdate(val data: WorkflowUpdateData) : WebSocketMessage()
        data class SystemStatus(val data: SystemStatusData) : WebSocketMessage()
        data class ConnectionEstablished(val userId: String) : WebSocketMessage()
        data class SubscriptionConfirmed(val queryId: String) : WebSocketMessage()
        data class Error(val message: String) : WebSocketMessage()
        object Heartbeat : WebSocketMessage()
        object Ping : WebSocketMessage()
    }

    fun connect() {
        if (webSocket != null) {
            Log.d(TAG, "WebSocket already connected")
            return
        }

        val token = encryptedPrefs.getAccessToken()
        if (token == null) {
            Log.e(TAG, "No auth token available")
            _connectionState.value = ConnectionState.ERROR("No authentication token")
            return
        }

        isManualDisconnect = false
        _connectionState.value = ConnectionState.CONNECTING

        val request = Request.Builder()
            .url("${BuildConfig.WS_BASE_URL}/v1/ws/query?token=$token")
            .build()

        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d(TAG, "WebSocket opened")
                reconnectAttempts = 0
                _connectionState.value = ConnectionState.CONNECTED
                startHeartbeat(webSocket)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                handleMessage(text)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closing: $code $reason")
                stopHeartbeat()
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closed: $code $reason")
                this@WebSocketManager.webSocket = null
                stopHeartbeat()
                _connectionState.value = ConnectionState.DISCONNECTED

                if (!isManualDisconnect && reconnectAttempts < maxReconnectAttempts) {
                    scheduleReconnect()
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "WebSocket error", t)
                this@WebSocketManager.webSocket = null
                stopHeartbeat()
                _connectionState.value = ConnectionState.ERROR(t.message ?: "Connection failed")

                if (!isManualDisconnect && reconnectAttempts < maxReconnectAttempts) {
                    scheduleReconnect()
                }
            }
        }

        webSocket = okHttpClient.newWebSocket(request, listener)
    }

    private fun startHeartbeat(webSocket: WebSocket) {
        heartbeatJob = CoroutineScope(Dispatchers.IO).launch {
            while (isActive) {
                delay(30000) // 30 seconds
                webSocket.send(
                    Json.encodeToString(
                        WebSocketMessage.serializer(),
                        WebSocketMessage.Heartbeat
                    )
                )
            }
        }
    }

    private fun stopHeartbeat() {
        heartbeatJob?.cancel()
        heartbeatJob = null
    }

    private fun scheduleReconnect() {
        reconnectAttempts++
        val delay = baseReconnectDelay * (2.0.pow(reconnectAttempts - 1)).toLong()
        
        Log.d(TAG, "Scheduling reconnect in ${delay}ms (attempt $reconnectAttempts)")
        
        CoroutineScope(Dispatchers.IO).launch {
            delay(delay)
            if (!isManualDisconnect) {
                connect()
            }
        }
    }

    private fun handleMessage(text: String) {
        try {
            val json = Json.parseToJsonElement(text).jsonObject
            val type = json["type"]?.jsonPrimitive?.contentOrNull ?: return

            CoroutineScope(Dispatchers.IO).launch {
                when (type) {
                    "connection_established" -> {
                        val userId = json["data"]?.jsonObject?.get("userId")?.jsonPrimitive?.content ?: ""
                        _messageFlow.emit(WebSocketMessage.ConnectionEstablished(userId))
                    }
                    
                    "query_update" -> {
                        val data = Json.decodeFromJsonElement<QueryUpdateData>(
                            json["data"]?.jsonObject ?: return@launch
                        )
                        _messageFlow.emit(WebSocketMessage.QueryUpdate(data))
                    }
                    
                    "workflow_update" -> {
                        val data = Json.decodeFromJsonElement<WorkflowUpdateData>(
                            json["data"]?.jsonObject ?: return@launch
                        )
                        _messageFlow.emit(WebSocketMessage.WorkflowUpdate(data))
                    }
                    
                    "subscription_confirmed" -> {
                        val queryId = json["data"]?.jsonObject?.get("queryId")?.jsonPrimitive?.content ?: ""
                        _messageFlow.emit(WebSocketMessage.SubscriptionConfirmed(queryId))
                    }
                    
                    "heartbeat" -> _messageFlow.emit(WebSocketMessage.Heartbeat)
                    
                    "ping" -> {
                        _messageFlow.emit(WebSocketMessage.Ping)
                        sendPong()
                    }
                    
                    "error" -> {
                        val message = json["data"]?.jsonObject?.get("message")?.jsonPrimitive?.content ?: "Unknown error"
                        _messageFlow.emit(WebSocketMessage.Error(message))
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse WebSocket message", e)
        }
    }

    fun sendMessage(message: Any) {
        val json = Json.encodeToString(message)
        webSocket?.send(json) ?: Log.w(TAG, "Cannot send message, WebSocket not connected")
    }

    fun subscribeToQuery(queryId: String) {
        sendMessage(mapOf(
            "type" to "subscribe_query",
            "queryId" to queryId,
            "timestamp" to Instant.now().toString()
        ))
    }

    fun submitQuery(query: String, operation: String = "general") {
        sendMessage(mapOf(
            "type" to "submit_query",
            "query" to query,
            "operation" to operation,
            "timestamp" to Instant.now().toString()
        ))
    }

    private fun sendPong() {
        sendMessage(mapOf(
            "type" to "pong",
            "timestamp" to Instant.now().toString()
        ))
    }

    fun disconnect() {
        isManualDisconnect = true
        reconnectAttempts = maxReconnectAttempts + 1
        stopHeartbeat()
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
        _connectionState.value = ConnectionState.DISCONNECTED
    }

    companion object {
        private const val TAG = "WebSocketManager"
    }
}

@Serializable
data class QueryUpdateData(
    val queryId: String,
    val status: String? = null,
    val chunk: String? = null,
    val complete: Boolean? = null,
    val responseText: String? = null,
    val verification: VerificationData? = null
)

@Serializable
data class WorkflowUpdateData(
    val workflowId: String,
    val stepId: String,
    val status: String,
    val progress: Int? = null,
    val result: String? = null,
    val error: String? = null
)
