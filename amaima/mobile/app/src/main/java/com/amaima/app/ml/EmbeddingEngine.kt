package com.amaima.app.ml

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.nio.FloatBuffer
import kotlin.math.sqrt

data class EmbeddingResult(
    val vector: FloatArray,
    val dimensions: Int,
    val modelName: String,
    val elapsedMs: Long
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as EmbeddingResult
        return vector.contentEquals(other.vector) && modelName == other.modelName
    }

    override fun hashCode(): Int {
        return vector.contentHashCode() + modelName.hashCode()
    }
}

class EmbeddingEngine(
    private val context: Context,
    private val ortEnvironment: OrtEnvironment
) {
    private var textSession: OrtSession? = null
    private var imageSession: OrtSession? = null
    private var embeddingDimensions: Int = 384

    companion object {
        private const val TAG = "EmbeddingEngine"
        private const val DEFAULT_TEXT_MODEL = "text_embedder"
        private const val DEFAULT_IMAGE_MODEL = "image_embedder"
        private const val MAX_SEQUENCE_LENGTH = 512
        private const val IMAGE_SIZE = 224
    }

    suspend fun loadTextModel(
        modelPath: String,
        dimensions: Int = 384
    ) = withContext(Dispatchers.IO) {
        try {
            val options = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }
            textSession = ortEnvironment.createSession(modelPath, options)
            embeddingDimensions = dimensions
            Log.d(TAG, "Text embedding model loaded: $dimensions dimensions")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load text embedding model", e)
        }
    }

    suspend fun loadImageModel(
        modelPath: String,
        dimensions: Int = 512
    ) = withContext(Dispatchers.IO) {
        try {
            val options = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }
            imageSession = ortEnvironment.createSession(modelPath, options)
            Log.d(TAG, "Image embedding model loaded: $dimensions dimensions")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load image embedding model", e)
        }
    }

    suspend fun embedText(text: String): EmbeddingResult = withContext(Dispatchers.Default) {
        val startTime = System.currentTimeMillis()
        val session = textSession
            ?: throw IllegalStateException("Text embedding model not loaded")

        val tokens = tokenize(text)
        val inputName = session.inputNames.first()

        val inputTensor = OnnxTensor.createTensor(
            ortEnvironment,
            FloatBuffer.wrap(tokens),
            longArrayOf(1, tokens.size.toLong())
        )

        val results = session.run(mapOf(inputName to inputTensor))
        val output = results[0].value as Array<FloatArray>
        val embedding = normalize(output[0])

        inputTensor.close()
        results.close()

        EmbeddingResult(
            vector = embedding,
            dimensions = embedding.size,
            modelName = DEFAULT_TEXT_MODEL,
            elapsedMs = System.currentTimeMillis() - startTime
        )
    }

    suspend fun embedTexts(texts: List<String>): List<EmbeddingResult> =
        withContext(Dispatchers.Default) {
            texts.map { embedText(it) }
        }

    suspend fun embedImage(bitmap: Bitmap): EmbeddingResult = withContext(Dispatchers.Default) {
        val startTime = System.currentTimeMillis()
        val session = imageSession
            ?: throw IllegalStateException("Image embedding model not loaded")

        val resized = Bitmap.createScaledBitmap(bitmap, IMAGE_SIZE, IMAGE_SIZE, true)
        val pixels = preprocessImage(resized)
        val inputName = session.inputNames.first()

        val inputTensor = OnnxTensor.createTensor(
            ortEnvironment,
            FloatBuffer.wrap(pixels),
            longArrayOf(1, 3, IMAGE_SIZE.toLong(), IMAGE_SIZE.toLong())
        )

        val results = session.run(mapOf(inputName to inputTensor))
        val output = results[0].value as Array<FloatArray>
        val embedding = normalize(output[0])

        inputTensor.close()
        results.close()

        EmbeddingResult(
            vector = embedding,
            dimensions = embedding.size,
            modelName = DEFAULT_IMAGE_MODEL,
            elapsedMs = System.currentTimeMillis() - startTime
        )
    }

    fun cosineSimilarity(a: FloatArray, b: FloatArray): Float {
        require(a.size == b.size) { "Vectors must have same dimensions" }
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

    private fun tokenize(text: String): FloatArray {
        val cleaned = text.lowercase().trim()
            .replace(Regex("[^a-z0-9\\s.,!?']"), "")

        val tokens = cleaned.split(Regex("\\s+"))
            .take(MAX_SEQUENCE_LENGTH)

        val vector = FloatArray(MAX_SEQUENCE_LENGTH) { 0f }
        tokens.forEachIndexed { index, token ->
            vector[index] = (token.hashCode().toLong() and 0xFFFFFFFFL).toFloat() / Int.MAX_VALUE.toFloat()
        }
        return vector
    }

    private fun preprocessImage(bitmap: Bitmap): FloatArray {
        val width = bitmap.width
        val height = bitmap.height
        val pixels = IntArray(width * height)
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height)

        val floats = FloatArray(3 * width * height)
        val mean = floatArrayOf(0.485f, 0.456f, 0.406f)
        val std = floatArrayOf(0.229f, 0.224f, 0.225f)

        for (i in pixels.indices) {
            val pixel = pixels[i]
            val r = ((pixel shr 16) and 0xFF) / 255f
            val g = ((pixel shr 8) and 0xFF) / 255f
            val b = (pixel and 0xFF) / 255f

            floats[i] = (r - mean[0]) / std[0]
            floats[width * height + i] = (g - mean[1]) / std[1]
            floats[2 * width * height + i] = (b - mean[2]) / std[2]
        }
        return floats
    }

    private fun normalize(vector: FloatArray): FloatArray {
        val norm = sqrt(vector.sumOf { (it * it).toDouble() }).toFloat()
        return if (norm > 0f) FloatArray(vector.size) { vector[it] / norm } else vector
    }

    fun close() {
        textSession?.close()
        imageSession?.close()
        textSession = null
        imageSession = null
    }
}
