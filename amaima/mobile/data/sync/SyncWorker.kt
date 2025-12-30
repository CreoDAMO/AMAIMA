// mobile/data/sync/SyncWorker.kt

@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val queryDao: QueryDao,
    private val workflowDao: WorkflowDao,
    private val fileDao: FileDao,
    private val api: AmaimaApi,
    private val networkMonitor: NetworkMonitor,
    private val preferences: UserPreferences
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        if (!networkMonitor.isOnline()) {
            Log.d(TAG, "No network, deferring sync")
            return Result.retry()
        }

        Log.d(TAG, "Starting background sync")

        return try {
            // Sync pending queries
            val queriesSynced = syncPendingQueries()
            Log.d(TAG, "Synced $queriesSynced queries")

            // Sync pending workflows
            val workflowsSynced = syncPendingWorkflows()
            Log.d(TAG, "Synced $workflowsSynced workflows")

            // Sync pending file uploads
            val filesSynced = syncPendingFileUploads()
            Log.d(TAG, "Synced $filesSynced files")

            // Sync settings
            syncSettings()

            // Fetch latest data
            fetchLatestData()

            // Update last sync timestamp
            preferences.updateLastSyncTime(System.currentTimeMillis())

            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Sync failed", e)
            
            if (runAttemptCount < 3) {
                Result.retry()
            } else {
                Result.failure()
            }
        }
    }

    private suspend fun syncPendingQueries(): Int {
        val pendingQueries = queryDao.getPendingQueries()
        var successCount = 0

        for (query in pendingQueries) {
            try {
                val response = api.submitQuery(QueryRequestDto(
                    query = query.queryText,
                    operation = query.operation,
                    metadata = query.metadata
                ))

                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    
                    // Update local query with server response
                    queryDao.updateQuery(query.copy(
                        responseText = result.responseText,
                        modelUsed = result.modelUsed,
                        confidence = result.confidence,
                        latencyMs = result.latencyMs,
                        status = QueryStatus.COMPLETED.name,
                        syncStatus = SyncStatus.SYNCED,
                        serverQueryId = result.queryId
                    ))
                    
                    successCount++
                    
                    // Show notification
                    showSyncNotification("Query synced", query.queryText.take(50))
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to sync query ${query.localId}", e)
            }
        }

        return successCount
    }

    private suspend fun syncPendingWorkflows(): Int {
        val pendingWorkflows = workflowDao.getPendingWorkflows()
        var successCount = 0

        for (workflow in pendingWorkflows) {
            try {
                val response = api.createWorkflow(workflow.toDto())

                if (response.isSuccessful && response.body() != null) {
                    workflowDao.updateWorkflow(workflow.copy(
                        serverId = response.body()!!.workflowId,
                        syncStatus = SyncStatus.SYNCED
                    ))
                    successCount++
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to sync workflow ${workflow.localId}", e)
            }
        }

        return successCount
    }

    private suspend fun syncPendingFileUploads(): Int {
        val pendingFiles = fileDao.getPendingUploads()
        var successCount = 0

        for (file in pendingFiles) {
            try {
                val fileEntity = File(file.localPath)
                val requestBody = fileEntity.asRequestBody("application/octet-stream".toMediaTypeOrNull())
                val multipartBody = MultipartBody.Part.createFormData(
                    "file",
                    fileEntity.name,
                    requestBody
                )

                val response = api.uploadFile(multipartBody)

                if (response.isSuccessful && response.body() != null) {
                    fileDao.updateFile(file.copy(
                        serverId = response.body()!!.fileId,
                        url = response.body()!!.url,
                        syncStatus = SyncStatus.SYNCED
                    ))
                    successCount++
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to sync file ${file.localId}", e)
            }
        }

        return successCount
    }

    private suspend fun syncSettings() {
        try {
            val response = api.getSettings()
            if (response.isSuccessful && response.body() != null) {
                preferences.updateSettings(response.body()!!.toSettings())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to sync settings", e)
        }
    }

    private suspend fun fetchLatestData() {
        // Fetch recent queries
        try {
            val response = api.getQueries(limit = 20)
            if (response.isSuccessful && response.body() != null) {
                response.body()!!.forEach { dto ->
                    queryDao.insertQuery(dto.toEntity())
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to fetch queries", e)
        }

        // Fetch active workflows
        try {
            val response = api.getWorkflows(status = "active")
            if (response.isSuccessful && response.body() != null) {
                response.body()!!.forEach { dto ->
                    workflowDao.insertWorkflow(dto.toEntity())
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to fetch workflows", e)
        }
    }

    private fun showSyncNotification(title: String, message: String) {
        val notificationManager = applicationContext.getSystemService(
            Context.NOTIFICATION_SERVICE
        ) as NotificationManager

        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(message)
            .setSmallIcon(R.drawable.ic_sync)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(NOTIFICATION_ID++, notification)
    }

    companion object {
        private const val TAG = "SyncWorker"
        private const val CHANNEL_ID = "amaima_sync"
        private var NOTIFICATION_ID = 1000

        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
                repeatInterval = 15,
                repeatIntervalTimeUnit = TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                syncRequest
            )
        }
    }
}
