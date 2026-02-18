package com.amaima.app.ml

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sqrt

data class VectorEntry(
    val id: String,
    val vector: FloatArray,
    val metadata: Map<String, String> = emptyMap(),
    val content: String = "",
    val timestamp: Long = System.currentTimeMillis()
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as VectorEntry
        return id == other.id
    }

    override fun hashCode(): Int = id.hashCode()
}

data class SearchResult(
    val entry: VectorEntry,
    val score: Float,
    val rank: Int
)

enum class SimilarityMetric {
    COSINE,
    EUCLIDEAN,
    DOT_PRODUCT
}

class VectorStore(
    private val dimensions: Int,
    private val maxEntries: Int = 10000,
    private val persistFile: File? = null
) {
    private val entries = mutableMapOf<String, VectorEntry>()
    private val mutex = Mutex()

    companion object {
        private const val TAG = "VectorStore"
        private const val MAGIC_BYTES = 0x56535452
        private const val VERSION = 1
    }

    init {
        persistFile?.let { loadFromDisk(it) }
    }

    suspend fun insert(entry: VectorEntry): Boolean = mutex.withLock {
        require(entry.vector.size == dimensions) {
            "Vector dimensions mismatch: expected $dimensions, got ${entry.vector.size}"
        }

        if (entries.size >= maxEntries && !entries.containsKey(entry.id)) {
            evictOldest()
        }

        entries[entry.id] = entry
        true
    }

    suspend fun insertBatch(batch: List<VectorEntry>): Int = mutex.withLock {
        var inserted = 0
        for (entry in batch) {
            if (entry.vector.size != dimensions) continue
            if (entries.size >= maxEntries && !entries.containsKey(entry.id)) {
                evictOldest()
            }
            entries[entry.id] = entry
            inserted++
        }
        inserted
    }

    suspend fun search(
        queryVector: FloatArray,
        topK: Int = 10,
        metric: SimilarityMetric = SimilarityMetric.COSINE,
        filter: ((VectorEntry) -> Boolean)? = null
    ): List<SearchResult> = mutex.withLock {
        require(queryVector.size == dimensions) {
            "Query vector dimensions mismatch: expected $dimensions, got ${queryVector.size}"
        }

        val candidates = if (filter != null) {
            entries.values.filter(filter)
        } else {
            entries.values.toList()
        }

        candidates
            .map { entry ->
                val score = when (metric) {
                    SimilarityMetric.COSINE -> cosineSimilarity(queryVector, entry.vector)
                    SimilarityMetric.EUCLIDEAN -> -euclideanDistance(queryVector, entry.vector)
                    SimilarityMetric.DOT_PRODUCT -> dotProduct(queryVector, entry.vector)
                }
                entry to score
            }
            .sortedByDescending { it.second }
            .take(topK)
            .mapIndexed { index, (entry, score) ->
                SearchResult(entry = entry, score = score, rank = index + 1)
            }
    }

    suspend fun searchByText(
        queryVector: FloatArray,
        topK: Int = 10,
        contentFilter: String? = null,
        metadataFilter: Map<String, String>? = null
    ): List<SearchResult> {
        val filter: ((VectorEntry) -> Boolean)? = if (contentFilter != null || metadataFilter != null) {
            { entry ->
                val contentMatch = contentFilter?.let {
                    entry.content.contains(it, ignoreCase = true)
                } ?: true

                val metadataMatch = metadataFilter?.all { (key, value) ->
                    entry.metadata[key] == value
                } ?: true

                contentMatch && metadataMatch
            }
        } else null

        return search(queryVector, topK, filter = filter)
    }

    suspend fun get(id: String): VectorEntry? = mutex.withLock {
        entries[id]
    }

    suspend fun delete(id: String): Boolean = mutex.withLock {
        entries.remove(id) != null
    }

    suspend fun deleteBatch(ids: List<String>): Int = mutex.withLock {
        var deleted = 0
        ids.forEach { if (entries.remove(it) != null) deleted++ }
        deleted
    }

    suspend fun clear(): Unit = mutex.withLock {
        entries.clear()
    }

    suspend fun size(): Int = mutex.withLock {
        entries.size
    }

    suspend fun contains(id: String): Boolean = mutex.withLock {
        entries.containsKey(id)
    }

    suspend fun getAllIds(): List<String> = mutex.withLock {
        entries.keys.toList()
    }

    suspend fun persist(): Boolean = withContext(Dispatchers.IO) {
        val file = persistFile ?: return@withContext false
        mutex.withLock {
            try {
                val raf = RandomAccessFile(file, "rw")
                raf.writeInt(MAGIC_BYTES)
                raf.writeInt(VERSION)
                raf.writeInt(dimensions)
                raf.writeInt(entries.size)

                for ((_, entry) in entries) {
                    val idBytes = entry.id.toByteArray(Charsets.UTF_8)
                    raf.writeInt(idBytes.size)
                    raf.write(idBytes)

                    val buffer = ByteBuffer.allocate(dimensions * 4).order(ByteOrder.LITTLE_ENDIAN)
                    entry.vector.forEach { buffer.putFloat(it) }
                    raf.write(buffer.array())

                    val contentBytes = entry.content.toByteArray(Charsets.UTF_8)
                    raf.writeInt(contentBytes.size)
                    raf.write(contentBytes)

                    val metaString = entry.metadata.entries.joinToString("\u0000") { "${it.key}\u0001${it.value}" }
                    val metaBytes = metaString.toByteArray(Charsets.UTF_8)
                    raf.writeInt(metaBytes.size)
                    raf.write(metaBytes)

                    raf.writeLong(entry.timestamp)
                }

                raf.close()
                Log.d(TAG, "Persisted ${entries.size} vectors to disk")
                true
            } catch (e: Exception) {
                Log.e(TAG, "Failed to persist vector store", e)
                false
            }
        }
    }

    private fun loadFromDisk(file: File) {
        if (!file.exists()) return
        try {
            val raf = RandomAccessFile(file, "r")
            val magic = raf.readInt()
            if (magic != MAGIC_BYTES) {
                raf.close()
                return
            }

            val version = raf.readInt()
            val dims = raf.readInt()
            val count = raf.readInt()

            if (dims != dimensions) {
                Log.w(TAG, "Dimension mismatch: expected $dimensions, file has $dims")
                raf.close()
                return
            }

            for (i in 0 until count) {
                val idLen = raf.readInt()
                val idBytes = ByteArray(idLen)
                raf.readFully(idBytes)
                val id = String(idBytes, Charsets.UTF_8)

                val vectorBytes = ByteArray(dimensions * 4)
                raf.readFully(vectorBytes)
                val vectorBuffer = ByteBuffer.wrap(vectorBytes).order(ByteOrder.LITTLE_ENDIAN)
                val vector = FloatArray(dimensions) { vectorBuffer.float }

                val contentLen = raf.readInt()
                val contentBytes = ByteArray(contentLen)
                raf.readFully(contentBytes)
                val content = String(contentBytes, Charsets.UTF_8)

                val metaLen = raf.readInt()
                val metaBytes = ByteArray(metaLen)
                raf.readFully(metaBytes)
                val metaString = String(metaBytes, Charsets.UTF_8)
                val metadata = if (metaString.isNotEmpty()) {
                    metaString.split("\u0000")
                        .filter { it.contains("\u0001") }
                        .associate {
                            val parts = it.split("\u0001", limit = 2)
                            parts[0] to parts[1]
                        }
                } else emptyMap()

                val timestamp = raf.readLong()

                entries[id] = VectorEntry(id, vector, metadata, content, timestamp)
            }

            raf.close()
            Log.d(TAG, "Loaded $count vectors from disk")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load vector store", e)
        }
    }

    private fun evictOldest() {
        val oldest = entries.values.minByOrNull { it.timestamp }
        oldest?.let { entries.remove(it.id) }
    }

    private fun cosineSimilarity(a: FloatArray, b: FloatArray): Float {
        var dot = 0f
        var normA = 0f
        var normB = 0f
        for (i in a.indices) {
            dot += a[i] * b[i]
            normA += a[i] * a[i]
            normB += b[i] * b[i]
        }
        val denom = sqrt(normA) * sqrt(normB)
        return if (denom > 0f) dot / denom else 0f
    }

    private fun euclideanDistance(a: FloatArray, b: FloatArray): Float {
        var sum = 0f
        for (i in a.indices) {
            val diff = a[i] - b[i]
            sum += diff * diff
        }
        return sqrt(sum)
    }

    private fun dotProduct(a: FloatArray, b: FloatArray): Float {
        var sum = 0f
        for (i in a.indices) {
            sum += a[i] * b[i]
        }
        return sum
    }
}
