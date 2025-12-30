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
