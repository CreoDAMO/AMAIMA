// android/ui/query/QueryViewModel.kt

@HiltViewModel
class QueryViewModel @Inject constructor(
    private val queryRepository: QueryRepository,
    private val fileRepository: FileRepository,
    private val webSocketManager: WebSocketManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(QueryUiState())
    val uiState: StateFlow<QueryUiState> = _uiState.asStateFlow()

    private val _queryResult = MutableStateFlow<QueryResult?>(null)
    val queryResult: StateFlow<QueryResult?> = _queryResult.asStateFlow()

    private val _streamingText = MutableStateFlow("")
    val streamingText: StateFlow<String> = _streamingText.asStateFlow()

    init {
        // Collect WebSocket messages
        viewModelScope.launch {
            webSocketManager.messageFlow.collect { message ->
                handleWebSocketMessage(message)
            }
        }
    }

    fun submitQuery(query: String, files: List<File>) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            try {
                // Upload files first
                val uploadedFiles = mutableListOf<FileMetadata>()
                if (files.isNotEmpty()) {
                    val uploadResult = fileRepository.uploadMultipleFiles(
                        files
                    ) { index, progress ->
                        _uiState.update {
                            it.copy(uploadProgress = progress * 100 / files.size)
                        }
                    }

                    uploadResult.fold(
                        onSuccess = { uploadedFiles.addAll(it) },
                        onFailure = { error ->
                            _uiState.update { it.copy(error = error.message) }
                            return@launch
                        }
                    )
                }

                // Submit query
                val request = QueryRequest(
                    query = query,
                    operation = "analysis",
                    fileIds = uploadedFiles.map { it.fileId },
                    context = mapOf("source" to "android")
                )

                val result = queryRepository.submitQuery(request)

                result.fold(
                    onSuccess = { queryResult ->
                        _queryResult.value = queryResult
                        _uiState.update { it.copy(isLoading = false) }

                        // Start WebSocket streaming if supported
                        if (queryResult.supportsStreaming) {
                            _uiState.update { it.copy(isStreaming = true) }
                            webSocketManager.submitQuery(query, "analysis")
                        }
                    },
                    onFailure = { error ->
                        _uiState.update {
                            it.copy(
                                isLoading = false,
                                error = error.message ?: "Query failed"
                            )
                        }
                    }
                )
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.message ?: "An error occurred"
                    )
                }
            }
        }
    }

    private fun handleWebSocketMessage(message: WebSocketMessage) {
        when (message) {
            is WebSocketMessage.QueryUpdate -> {
                message.data.chunk?.let { chunk ->
                    _streamingText.update { it + chunk }
                }

                if (message.data.complete == true) {
                    _uiState.update { it.copy(isStreaming = false) }
                    // Update final result
                    _queryResult.value = _queryResult.value?.copy(
                        responseText = _streamingText.value
                    )
                }
            }
            is WebSocketMessage.Error -> {
                _uiState.update {
                    it.copy(
                        isStreaming = false,
                        error = message.message
                    )
                }
            }
            else -> {}
        }
    }

    fun clearQuery() {
        _queryResult.value = null
        _streamingText.value = ""
        _uiState.update { QueryUiState() }
    }
}

data class QueryUiState(
    val isLoading: Boolean = false,
    val isStreaming: Boolean = false,
    val uploadProgress: Float = 0f,
    val error: String? = null
)
