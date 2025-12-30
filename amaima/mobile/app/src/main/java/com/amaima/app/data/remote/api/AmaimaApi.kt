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
