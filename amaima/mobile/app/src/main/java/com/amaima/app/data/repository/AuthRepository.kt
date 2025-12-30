// data/repository/AuthRepository.kt

interface AuthRepository {
    val authState: StateFlow<AuthState>
    
    suspend fun login(email: String, password: String): Result<User>
    suspend fun register(name: String, email: String, password: String): Result<User>
    suspend fun logout(): Result<Unit>
    suspend fun refreshToken(): Result<String>
    suspend fun getCurrentUser(): Result<User>
    suspend fun isAuthenticated(): Boolean
}

class AuthRepositoryImpl(
    private val api: AmaimaApi,
    private val encryptedPrefs: EncryptedPreferences,
    private val userDao: UserDao
) : AuthRepository {

    private val _authState = MutableStateFlow<AuthState>(AuthState.Loading)
    override val authState: StateFlow<AuthState> = _authState.asStateFlow()

    init {
        CoroutineScope(Dispatchers.IO).launch {
            initializeAuth()
        }
    }

    private suspend fun initializeAuth() {
        val accessToken = encryptedPrefs.getAccessToken()
        val refreshToken = encryptedPrefs.getRefreshToken()

        if (accessToken == null || refreshToken == null) {
            _authState.value = AuthState.Unauthenticated
            return
        }

        try {
            // Check token expiration
            if (isTokenExpired(accessToken)) {
                val refreshSuccess = refreshToken() == null
                if (!refreshSuccess) {
                    _authState.value = AuthState.Unauthenticated
                    return
                }
            }

            // Verify with backend
            val response = api.getCurrentUser()
            if (response.isSuccessful) {
                response.body()?.let { userDto ->
                    val user = userDto.toDomain()
                    userDao.insertUser(user.toEntity())
                    _authState.value = AuthState.Authenticated(user)
                }
            } else {
                clearAuthData()
                _authState.value = AuthState.Unauthenticated
            }
        } catch (e: Exception) {
            Log.e(TAG, "Auth initialization failed", e)
            clearAuthData()
            _authState.value = AuthState.Unauthenticated
        }
    }

    override suspend fun login(email: String, password: String): Result<User> {
        return withContext(Dispatchers.IO) {
            try {
                _authState.value = AuthState.Loading

                val response = api.login(LoginRequestDto(email, password))

                if (response.isSuccessful && response.body() != null) {
                    val loginResponse = response.body()!!

                    // Store tokens securely
                    encryptedPrefs.saveAccessToken(loginResponse.accessToken)
                    encryptedPrefs.saveRefreshToken(loginResponse.refreshToken)
                    encryptedPrefs.saveUserId(loginResponse.user.id)

                    // Store user in local database
                    val user = loginResponse.user.toDomain()
                    userDao.insertUser(user.toEntity())

                    _authState.value = AuthState.Authenticated(user)

                    Result.success(user)
                } else {
                    val errorMsg = response.body()?.error?.message ?: "Login failed"
                    _authState.value = AuthState.Error(errorMsg)
                    Result.failure(Exception(errorMsg))
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Unknown error")
                Result.failure(e)
            }
        }
    }

    override suspend fun logout(): Result<Unit> {
        return withContext(Dispatchers.IO) {
            try {
                val refreshToken = encryptedPrefs.getRefreshToken()

                // Notify server of logout (to blacklist refresh token)
                if (refreshToken != null) {
                    api.logout(LogoutRequestDto(refreshToken))
                }

                // Clear all local data
                clearAuthData()
                userDao.deleteAllUsers()

                _authState.value = AuthState.Unauthenticated

                Result.success(Unit)
            } catch (e: Exception) {
                // Still clear local data even if server call fails
                clearAuthData()
                userDao.deleteAllUsers()
                _authState.value = AuthState.Unauthenticated

                Result.success(Unit) // Consider this a success
            }
        }
    }

    override suspend fun refreshToken(): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val refreshToken = encryptedPrefs.getRefreshToken()
                    ?: return@withContext Result.failure(Exception("No refresh token"))

                val response = api.refreshToken(RefreshTokenRequestDto(refreshToken))

                if (response.isSuccessful && response.body() != null) {
                    val tokenResponse = response.body()!!

                    encryptedPrefs.saveAccessToken(tokenResponse.accessToken)
                    encryptedPrefs.saveRefreshToken(tokenResponse.refreshToken)

                    Result.success(tokenResponse.accessToken)
                } else {
                    // Refresh failed - user needs to re-authenticate
                    logout()
                    Result.failure(Exception("Token refresh failed"))
                }
            } catch (e: Exception) {
                logout()
                Result.failure(e)
            }
        }
    }

    private fun clearAuthData() {
        encryptedPrefs.clearAuthData()
    }

    private fun isTokenExpired(token: String): Boolean {
        return try {
            val claims = decodeJwt(token)
            val exp = claims["exp"] as Number
            System.currentTimeMillis() / 1000 >= exp.toLong()
        } catch (e: Exception) {
            true
        }
    }

    private fun decodeJwt(token: String): Map<String, Any> {
        val parts = token.split(".")
        val payload = parts[1]
        val decoded = Base64.getUrlDecoder().decode(payload)
        val json = String(decoded, Charset.forName("UTF-8"))
        return Gson().fromJson(json, object : TypeToken<Map<String, Any>>() {}.type)
    }

    companion object {
        private const val TAG = "AuthRepository"
    }
}

sealed class AuthState {
    object Loading : AuthState()
    object Unauthenticated : AuthState()
    data class Authenticated(val user: User) : AuthState()
    data class Error(val message: String) : AuthState()
}
