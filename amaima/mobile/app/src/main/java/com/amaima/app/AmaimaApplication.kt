class AmaimaApplication : Application() {

    lateinit var appContainer: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        
        initializeDependencyInjection()
        initializeCrashReporting()
        initializeAnalytics()
        initializeMlCapabilities()
        
        registerActivityLifecycleCallbacks(ActivityLifecycleHandler())
    }

    private fun initializeDependencyInjection() {
        appContainer = AppContainer(this)
    }

    private fun initializeCrashReporting() {
        if (BuildConfig.DEBUG.not()) {
            Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
                CrashReporter.reportException(throwable)
                DefaultUncaughtExceptionHandler.uncaughtException(thread, throwable)
            }
        }
    }

    private fun initializeAnalytics() {
        Analytics.initialize(this)
        Analytics.trackEvent(AnalyticsEvent.APP_OPENED)
    }

    private fun initializeMlCapabilities() {
        CoroutineScope(Dispatchers.Default).launch {
            try {
                val mlManager = appContainer.mlManager
                mlManager.loadDefaultModels()
                Log.d(TAG, "ML capabilities initialized successfully")
            } catch (e: Exception) {
                Log.w(TAG, "Failed to initialize ML capabilities", e)
            }
        }
    }

    companion object {
        private const val TAG = "AmaimaApplication"
        
        @Volatile
        private var instance: AmaimaApplication? = null
        
        fun getInstance(): AmaimaApplication {
            return instance ?: throw IllegalStateException(
                "Application not initialized"
            )
        }
    }
}
