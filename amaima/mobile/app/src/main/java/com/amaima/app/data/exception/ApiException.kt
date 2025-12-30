// data/exception/ApiException.kt

sealed class ApiException(
    message: String,
    val code: String,
    val details: List<ErrorDetail>? = null
) : Exception(message) {
    data class ErrorDetail(
        val field: String,
        val message: String,
        val type: String
    )

    // Authentication errors
    data class TokenExpired(override val message: String) : ApiException(
        message, "AUTH_TOKEN_EXPIRED"
    )

    data class Unauthorized(override val message: String) : ApiException(
        message, "AUTH_PERMISSION_DENIED"
    )

    // Validation errors
    data class ValidationFailed(
        override val details: List<ErrorDetail>,
        message: String = "Validation failed"
    ) : ApiException(message, "VALIDATION_ERROR", details)

    // System errors
    data class RateLimited(override val message: String) : ApiException(
        message, "SYSTEM_RATE_LIMITED"
    )

    data class ServiceUnavailable(override val message: String) : ApiException(
        message, "SYSTEM_UNAVAILABLE"
    )

    data class InternalError(override val message: String) : ApiException(
        message, "SYSTEM_INTERNAL_ERROR"
    )

    companion object {
        fun fromResponse(response: Response<*>): ApiException {
            val errorBody = response.errorBody()?.string() ?: return InternalError("Unknown error")

            return try {
                val json = Json.parseToJsonElement(errorBody).jsonObject
                val error = json["error"]?.jsonObject
                val meta = json["meta"]?.jsonObject

                val code = error?.get("code")?.jsonPrimitive?.content ?: "UNKNOWN"
                val message = error?.get("message")?.jsonPrimitive?.content ?: "Unknown error"
                val details = error?.get("details")?.jsonArray
                    ?.map { element ->
                        val detailObj = element.jsonObject
                        ErrorDetail(
                            field = detailObj["field"]?.jsonPrimitive?.content ?: "",
                            message = detailObj["message"]?.jsonPrimitive?.content ?: "",
                            type = detailObj["type"]?.jsonPrimitive?.content ?: ""
                        )
                    }

                when (code) {
                    "AUTH_TOKEN_EXPIRED" -> TokenExpired(message)
                    "AUTH_PERMISSION_DENIED" -> Unauthorized(message)
                    "VALIDATION_ERROR" -> ValidationFailed(details ?: emptyList(), message)
                    "SYSTEM_RATE_LIMITED" -> RateLimited(message)
                    "SYSTEM_UNAVAILABLE" -> ServiceUnavailable(message)
                    else -> InternalError(message)
                }
            } catch (e: Exception) {
                InternalError("Failed to parse error response")
            }
        }
    }
}

// Exception mapper for Retrofit
class ExceptionMapper<T> : Converter<ResponseBody, T> {
    override fun convert(value: ResponseBody): T? {
        val error = ApiException.fromResponse(
            Response.error<T>(500, value, Retrofit.Builder().baseUrl("").build())
        )
        throw error as? T ?: throw error
    }
}

// Global error handler
object GlobalErrorHandler {
    private val errorHandlers = mutableMapOf<String, (ApiException) -> Unit>()

    init {
        // Register default handlers
        registerHandler("AUTH_TOKEN_EXPIRED") { exception ->
            // Trigger token refresh
            CoroutineScope(Dispatchers.Main).launch {
                val authRepository = get<AuthRepository>()
                authRepository.refreshToken()
            }
        }

        registerHandler("AUTH_PERMISSION_DENIED") { exception ->
            // Navigate to unauthorized screen
            navController.navigate("unauthorized")
        }

        registerHandler("VALIDATION_ERROR") { exception ->
            // Show validation errors
            exception.details?.forEach { detail ->
                showFieldError(detail.field, detail.message)
            }
        }

        registerHandler("SYSTEM_RATE_LIMITED") { exception ->
            // Show rate limit toast
            showToast("Too many requests. Please wait.")
        }
    }

    fun handle(exception: Exception) {
        when (exception) {
            is ApiException -> {
                val handler = errorHandlers[exception.code]
                handler?.invoke(exception) ?: defaultHandler(exception)
            }
            else -> {
                defaultHandler(exception)
            }
        }
    }

    private fun defaultHandler(exception: Exception) {
        showToast(exception.message ?: "An error occurred")
    }

    fun registerHandler(code: String, handler: (ApiException) -> Unit) {
        errorHandlers[code] = handler
    }
}
