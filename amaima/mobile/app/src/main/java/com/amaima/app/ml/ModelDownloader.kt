package com.amaima.app.ml

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

class ModelDownloader(
    private val context: Context,
    private val okHttpClient: OkHttpClient
) {
    companion object {
        private const val TAG = "ModelDownloader"
        private const val MODEL_BASE_URL = "https://api.amaima.example.com/v1/models/download"
    }

    suspend fun downloadModel(
        modelName: String,
        targetFile: File,
        onProgress: ((Float) -> Unit)? = null
    ): Boolean = withContext(Dispatchers.IO) {
        try {
            targetFile.parentFile?.mkdirs()

            val assetPath = "models/$modelName"
            val assetModels = try {
                context.assets.list("models") ?: emptyArray()
            } catch (e: Exception) {
                emptyArray()
            }

            val matchingAsset = assetModels.firstOrNull { it.startsWith(modelName) }
            if (matchingAsset != null) {
                Log.d(TAG, "Loading model from assets: $matchingAsset")
                context.assets.open("models/$matchingAsset").use { input ->
                    FileOutputStream(targetFile).use { output ->
                        input.copyTo(output)
                    }
                }
                onProgress?.invoke(1f)
                return@withContext true
            }

            Log.d(TAG, "Downloading model from server: $modelName")
            val url = "$MODEL_BASE_URL/$modelName"
            val request = Request.Builder()
                .url(url)
                .build()

            val response = okHttpClient.newCall(request).execute()

            if (!response.isSuccessful) {
                Log.w(TAG, "Download failed: ${response.code}")
                response.close()
                return@withContext false
            }

            val body = response.body ?: run {
                response.close()
                return@withContext false
            }

            val totalBytes = body.contentLength()
            var downloadedBytes = 0L

            body.byteStream().use { input ->
                FileOutputStream(targetFile).use { output ->
                    val buffer = ByteArray(8192)
                    var bytesRead: Int
                    while (input.read(buffer).also { bytesRead = it } != -1) {
                        output.write(buffer, 0, bytesRead)
                        downloadedBytes += bytesRead
                        if (totalBytes > 0) {
                            onProgress?.invoke(downloadedBytes.toFloat() / totalBytes)
                        }
                    }
                }
            }

            response.close()
            onProgress?.invoke(1f)
            Log.d(TAG, "Model downloaded: $modelName (${targetFile.length() / 1024}KB)")
            true
        } catch (e: IOException) {
            Log.e(TAG, "Download error for model: $modelName", e)
            targetFile.delete()
            false
        } catch (e: Exception) {
            Log.e(TAG, "Unexpected error downloading model: $modelName", e)
            targetFile.delete()
            false
        }
    }

    fun getModelCacheDir(): File {
        val dir = File(context.filesDir, "models")
        dir.mkdirs()
        return dir
    }

    fun getCachedModels(): List<File> {
        return getModelCacheDir().listFiles()
            ?.filter { it.isFile }
            ?.toList()
            ?: emptyList()
    }

    fun isModelCached(modelName: String): Boolean {
        val cacheDir = getModelCacheDir()
        return cacheDir.listFiles()?.any { it.name.startsWith(modelName) } ?: false
    }
}
