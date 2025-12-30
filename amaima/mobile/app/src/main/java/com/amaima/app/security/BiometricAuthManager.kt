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
