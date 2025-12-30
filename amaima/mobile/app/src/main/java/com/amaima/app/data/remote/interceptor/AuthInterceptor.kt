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
