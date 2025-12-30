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
