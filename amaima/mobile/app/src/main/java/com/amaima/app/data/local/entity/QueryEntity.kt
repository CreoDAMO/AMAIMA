@Entity(
    tableName = "queries",
    indices = [
        Index(value = ["queryId"], unique = true),
        Index(value = ["timestamp"]),
        Index(value = ["status"])
    ]
)
data class QueryEntity(
    @PrimaryKey
    @ColumnInfo(name = "query_id")
    val queryId: String,

    @ColumnInfo(name = "query_text")
    val queryText: String,

    @ColumnInfo(name = "response_text")
    val responseText: String? = null,

    @ColumnInfo(name = "model_used")
    val modelUsed: String? = null,

    @ColumnInfo(name = "complexity")
    val complexity: String,

    @ColumnInfo(name = "execution_mode")
    val executionMode: String,

    @ColumnInfo(name = "confidence")
    val confidence: Float,

    @ColumnInfo(name = "latency_ms")
    val latencyMs: Float,

    @ColumnInfo(name = "status")
    val status: String,

    @ColumnInfo(name = "feedback_type")
    val feedbackType: String? = null,

    @ColumnInfo(name = "timestamp")
    val timestamp: Long,

    @ColumnInfo(name = "sync_status")
    val syncStatus: Int = SyncStatus.SYNCED
)

@Entity(
    tableName = "workflows",
    indices = [
        Index(value = ["workflowId"], unique = true),
        Index(value = ["status"]),
        Index(value = ["timestamp"])
    ]
)
data class WorkflowEntity(
    @PrimaryKey
    @ColumnInfo(name = "workflow_id")
    val workflowId: String,

    @ColumnInfo(name = "name")
    val name: String,

    @ColumnInfo(name = "description")
    val description: String? = null,

    @ColumnInfo(name = "total_steps")
    val totalSteps: Int,

    @ColumnInfo(name = "completed_steps")
    val completedSteps: Int,

    @ColumnInfo(name = "status")
    val status: String,

    @ColumnInfo(name = "results")
    val results: String? = null,

    @ColumnInfo(name = "duration_ms")
    val durationMs: Float,

    @ColumnInfo(name = "timestamp")
    val timestamp: Long,

    @ColumnInfo(name = "sync_status")
    val syncStatus: Int = SyncStatus.SYNCED
)

@Entity(
    tableName = "users",
    indices = [Index(value = ["userId"], unique = true)]
)
data class UserEntity(
    @PrimaryKey
    @ColumnInfo(name = "user_id")
    val userId: String,

    @ColumnInfo(name = "email")
    val email: String,

    @ColumnInfo(name = "display_name")
    val displayName: String? = null,

    @ColumnInfo(name = "avatar_url")
    val avatarUrl: String? = null,

    @ColumnInfo(name = "preferences")
    val preferences: String? = null,

    @ColumnInfo(name = "last_active")
    val lastActive: Long
)

object SyncStatus {
    const val SYNCED = 0
    const val PENDING_UPLOAD = 1
    const val PENDING_DOWNLOAD = 2
    const val CONFLICT = 3
}

@Dao
interface QueryDao {

    @Query("SELECT * FROM queries ORDER BY timestamp DESC")
    fun getAllQueries(): Flow<List<QueryEntity>>

    @Query("SELECT * FROM queries WHERE status = :status ORDER BY timestamp DESC")
    fun getQueriesByStatus(status: String): Flow<List<QueryEntity>>

    @Query("SELECT * FROM queries WHERE query_id = :queryId")
    suspend fun getQueryById(queryId: String): QueryEntity?

    @Query("SELECT * FROM queries WHERE sync_status = :syncStatus")
    suspend fun getQueriesBySyncStatus(syncStatus: Int): List<QueryEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQuery(query: QueryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQueries(queries: List<QueryEntity>)

    @Update
    suspend fun updateQuery(query: QueryEntity)

    @Query("UPDATE queries SET sync_status = :syncStatus WHERE query_id = :queryId")
    suspend fun updateSyncStatus(queryId: String, syncStatus: Int)

    @Query("UPDATE queries SET feedback_type = :feedbackType WHERE query_id = :queryId")
    suspend fun updateFeedback(queryId: String, feedbackType: String)

    @Query("DELETE FROM queries WHERE query_id = :queryId")
    suspend fun deleteQuery(queryId: String)

    @Query("DELETE FROM queries WHERE timestamp < :timestamp")
    suspend fun deleteOldQueries(timestamp: Long)
}

@Dao
interface WorkflowDao {

    @Query("SELECT * FROM workflows ORDER BY timestamp DESC")
    fun getAllWorkflows(): Flow<List<WorkflowEntity>>

    @Query("SELECT * FROM workflows WHERE status = :status ORDER BY timestamp DESC")
    fun getWorkflowsByStatus(status: String): Flow<List<WorkflowEntity>>

    @Query("SELECT * FROM workflows WHERE workflow_id = :workflowId")
    suspend fun getWorkflowById(workflowId: String): WorkflowEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertWorkflow(workflow: WorkflowEntity)

    @Update
    suspend fun updateWorkflow(workflow: WorkflowEntity)

    @Query("UPDATE workflows SET status = :status, completed_steps = :completedSteps WHERE workflow_id = :workflowId")
    suspend fun updateWorkflowProgress(workflowId: String, status: String, completedSteps: Int)

    @Query("DELETE FROM workflows WHERE workflow_id = :workflowId")
    suspend fun deleteWorkflow(workflowId: String)
}

@Database(
    entities = [QueryEntity::class, WorkflowEntity::class, UserEntity::class],
    version = 1,
    exportSchema = true
)
abstract class AmaimaDatabase : RoomDatabase() {
    abstract fun queryDao(): QueryDao
    abstract fun workflowDao(): WorkflowDao
    abstract fun userDao(): UserDao
}
