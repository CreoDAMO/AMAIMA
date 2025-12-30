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
