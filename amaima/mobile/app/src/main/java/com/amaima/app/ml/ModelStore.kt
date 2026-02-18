package com.amaima.app.ml

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

class ModelStore(
    private val context: Context,
    private val modelDownloader: ModelDownloader
) {
    private val modelsDir: File = File(context.filesDir, "models")
    private val checksumFile: File = File(modelsDir, ".checksums")

    companion object {
        private const val TAG = "ModelStore"
        private const val MAX_CACHE_SIZE_BYTES = 500L * 1024 * 1024
    }

    init {
        modelsDir.mkdirs()
    }

    suspend fun ensureModelAvailable(
        metadata: ModelMetadata,
        onProgress: (Float) -> Unit = {}
    ): File? = withContext(Dispatchers.IO) {
        val modelFile = getModelFile(metadata)

        if (modelFile.exists() && verifyChecksum(metadata, modelFile)) {
            Log.d(TAG, "Model cached: ${metadata.name}")
            return@withContext modelFile
        }

        try {
            modelFile.parentFile?.mkdirs()
            val downloaded = modelDownloader.downloadModel(metadata.name, modelFile)
            if (downloaded) {
                saveChecksum(metadata, modelFile)
                enforceMaxCacheSize()
                Log.d(TAG, "Model downloaded: ${metadata.name}")
                modelFile
            } else {
                Log.w(TAG, "Download failed: ${metadata.name}")
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error ensuring model: ${metadata.name}", e)
            null
        }
    }

    fun getModelFile(metadata: ModelMetadata): File {
        val fileName = when (metadata.precision) {
            ModelPrecision.FP32 -> metadata.modelPath
            else -> {
                val base = metadata.modelPath.substringBeforeLast(".")
                val ext = metadata.modelPath.substringAfterLast(".")
                "${base}_${metadata.precision.name.lowercase()}.$ext"
            }
        }
        return File(context.filesDir, fileName)
    }

    fun isModelCached(metadata: ModelMetadata): Boolean {
        return getModelFile(metadata).exists()
    }

    suspend fun deleteModel(metadata: ModelMetadata): Boolean = withContext(Dispatchers.IO) {
        val file = getModelFile(metadata)
        if (file.exists()) {
            val deleted = file.delete()
            if (deleted) removeChecksum(metadata)
            deleted
        } else false
    }

    suspend fun getCacheSize(): Long = withContext(Dispatchers.IO) {
        modelsDir.walkTopDown()
            .filter { it.isFile && !it.name.startsWith(".") }
            .sumOf { it.length() }
    }

    suspend fun clearCache(): Unit = withContext(Dispatchers.IO) {
        modelsDir.listFiles()
            ?.filter { !it.name.startsWith(".") }
            ?.forEach { it.delete() }
        checksumFile.delete()
        Log.d(TAG, "Cache cleared")
    }

    private fun verifyChecksum(metadata: ModelMetadata, file: File): Boolean {
        val storedChecksums = loadChecksums()
        val storedHash = storedChecksums[metadata.name] ?: return true
        val fileHash = computeSha256(file)
        return storedHash == fileHash
    }

    private fun computeSha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().buffered().use { stream ->
            val buffer = ByteArray(8192)
            var bytesRead: Int
            while (stream.read(buffer).also { bytesRead = it } != -1) {
                digest.update(buffer, 0, bytesRead)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }

    private fun saveChecksum(metadata: ModelMetadata, file: File) {
        val checksums = loadChecksums().toMutableMap()
        checksums[metadata.name] = computeSha256(file)
        checksumFile.writeText(checksums.entries.joinToString("\n") { "${it.key}=${it.value}" })
    }

    private fun removeChecksum(metadata: ModelMetadata) {
        val checksums = loadChecksums().toMutableMap()
        checksums.remove(metadata.name)
        checksumFile.writeText(checksums.entries.joinToString("\n") { "${it.key}=${it.value}" })
    }

    private fun loadChecksums(): Map<String, String> {
        if (!checksumFile.exists()) return emptyMap()
        return checksumFile.readLines()
            .filter { it.contains("=") }
            .associate {
                val (key, value) = it.split("=", limit = 2)
                key to value
            }
    }

    private suspend fun enforceMaxCacheSize() {
        val cacheSize = getCacheSize()
        if (cacheSize <= MAX_CACHE_SIZE_BYTES) return

        val files = modelsDir.listFiles()
            ?.filter { it.isFile && !it.name.startsWith(".") }
            ?.sortedBy { it.lastModified() }
            ?: return

        var currentSize = cacheSize
        for (file in files) {
            if (currentSize <= MAX_CACHE_SIZE_BYTES) break
            val fileSize = file.length()
            file.delete()
            currentSize -= fileSize
            Log.d(TAG, "Evicted model: ${file.name} (${fileSize / 1024}KB)")
        }
    }
}
