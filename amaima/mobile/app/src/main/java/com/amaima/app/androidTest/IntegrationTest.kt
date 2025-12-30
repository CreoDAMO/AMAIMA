// amaima/mobile/app/src/main/java/com/amaima/app/androidTest/IntegrationTest.kt

@RunWith(AndroidJUnit4::class)
@LargeTest
class IntegrationTest {

    @get:Rule
    val hiltRule = HiltAndroidRule(this)

    private lateinit var authRepository: AuthRepository
    private lateinit var queryRepository: QueryRepository
    private lateinit var webSocketManager: WebSocketManager

    @Before
    fun setup() {
        hiltRule.inject()
        authRepository = AuthRepositoryImpl(...)
        queryRepository = QueryRepositoryImpl(...)
        webSocketManager = WebSocketManager(...)
    }

    @Test
    fun authenticationFlow() = runBlocking {
        // Test registration
        val registerResult = authRepository.register(
            name = "Test User",
            email = "test${System.currentTimeMillis()}@example.com",
            password = "TestPass123!"
        )

        assertTrue(registerResult.isSuccess)
        assertNotNull(registerResult.getOrNull())

        // Test login with new credentials
        val loginResult = authRepository.login(
            email = registerResult.getOrNull()!!.email,
            password = "TestPass123!"
        )

        assertTrue(loginResult.isSuccess)
        assertEquals(registerResult.getOrNull()!!.id, loginResult.getOrNull()!!.id)

        // Test logout
        val logoutResult = authRepository.logout()
        assertTrue(logoutResult.isSuccess)
    }

    @Test
    fun querySubmissionAndStreaming() = runBlocking {
        // Login
        authRepository.login("test@example.com", "password123")

        // Connect WebSocket
        webSocketManager.connect()
        delay(2000)

        assertTrue(webSocketManager.connectionState.value == ConnectionState.CONNECTED)

        // Submit streaming query
        val queryText = "Explain how quantum computing works"
        webSocketManager.submitQuery(queryText, "general")

        // Collect streaming response
        val chunks = mutableListOf<String>()
        val completionLatch = CountDownLatch(1)

        val job = launch {
            webSocketManager.messageFlow
                .filterIsInstance<WebSocketMessage.QueryUpdate>()
                .collect { message ->
                    message.data.chunk?.let { chunks.add(it) }
                    if (message.data.complete == true) {
                        completionLatch.countDown()
                        cancel()
                    }
                }
        }

        // Wait for completion or timeout
        assertTrue(completionLatch.await(120, TimeUnit.SECONDS))

        // Verify streaming
        assertTrue(chunks.isNotEmpty())
        assertTrue(chunks.joinToString(" ").contains("quantum"))

        webSocketManager.disconnect()
    }

    @Test
    fun offlineQueryQueueAndSync() = runBlocking {
        // Enable airplane mode simulation
        networkMonitor.setOnline(false)

        // Submit query while offline
        val queryResult = queryRepository.submitQuery(
            QueryRequest(query = "Offline query test", operation = "general")
        )

        // Should be queued locally
        assertTrue(queryResult.isFailure)

        // Verify query is queued
        val pendingQueries = queryDao.getPendingQueries()
        assertEquals(1, pendingQueries.size)

        // Simulate coming back online
        networkMonitor.setOnline(true)

        // Trigger sync
        val syncWorker = SyncWorker(appContext, workerParams)
        syncWorker.doWork()

        // Verify query was synced
        val syncedQueries = queryDao.getQueriesBySyncStatus(SyncStatus.SYNCED)
        assertTrue(syncedQueries.any { it.queryText.contains("Offline query test") })
    }
}
