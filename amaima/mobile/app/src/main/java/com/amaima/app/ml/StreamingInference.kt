package com.amaima.app.ml

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.isActive
import java.nio.FloatBuffer
import java.util.concurrent.atomic.AtomicBoolean

data class StreamingChunk(
    val tokenId: Int = -1,
    val text: String = "",
    val probabilities: FloatArray? = null,
    val isFirst: Boolean = false,
    val isFinal: Boolean = false,
    val chunkIndex: Int = 0,
    val elapsedMs: Long = 0L
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as StreamingChunk
        return tokenId == other.tokenId && text == other.text && chunkIndex == other.chunkIndex
    }

    override fun hashCode(): Int {
        var result = tokenId
        result = 31 * result + text.hashCode()
        result = 31 * result + chunkIndex
        return result
    }
}

data class StreamingConfig(
    val maxTokens: Int = 256,
    val temperature: Float = 0.7f,
    val topK: Int = 50,
    val chunkSize: Int = 1,
    val stopTokenIds: Set<Int> = emptySet()
)

class StreamingSession(
    private val ortEnvironment: OrtEnvironment,
    private val session: OrtSession,
    private val config: StreamingConfig = StreamingConfig()
) {
    private val isActive = AtomicBoolean(false)
    private var kvCache: MutableMap<String, OnnxTensor>? = null

    companion object {
        private const val TAG = "StreamingSession"
    }

    fun streamInference(
        inputIds: IntArray,
        attentionMask: IntArray? = null
    ): Flow<StreamingChunk> = callbackFlow {
        isActive.set(true)
        val startTime = System.currentTimeMillis()

        try {
            var currentIds = inputIds.toMutableList()
            var tokenIndex = 0

            while (isActive.get() && isActive() && tokenIndex < config.maxTokens) {
                val inputTensor = OnnxTensor.createTensor(
                    ortEnvironment,
                    arrayOf(currentIds.toIntArray())
                )

                val inputs = mutableMapOf<String, OnnxTensor>()
                val inputName = session.inputNames.first()
                inputs[inputName] = inputTensor

                if (attentionMask != null || tokenIndex > 0) {
                    val mask = attentionMask ?: IntArray(currentIds.size) { 1 }
                    val paddedMask = if (mask.size < currentIds.size) {
                        IntArray(currentIds.size) { if (it < mask.size) mask[it] else 1 }
                    } else mask

                    if (session.inputNames.contains("attention_mask")) {
                        inputs["attention_mask"] = OnnxTensor.createTensor(
                            ortEnvironment,
                            arrayOf(paddedMask)
                        )
                    }
                }

                val results = session.run(inputs)
                val logits = results[0].value as Array<Array<FloatArray>>
                val lastLogits = logits[0].last()

                val nextTokenId = sampleToken(lastLogits, config.temperature, config.topK)

                if (nextTokenId in config.stopTokenIds) {
                    trySend(
                        StreamingChunk(
                            tokenId = nextTokenId,
                            isFinal = true,
                            chunkIndex = tokenIndex,
                            elapsedMs = System.currentTimeMillis() - startTime
                        )
                    )
                    break
                }

                trySend(
                    StreamingChunk(
                        tokenId = nextTokenId,
                        probabilities = lastLogits,
                        isFirst = tokenIndex == 0,
                        isFinal = tokenIndex == config.maxTokens - 1,
                        chunkIndex = tokenIndex,
                        elapsedMs = System.currentTimeMillis() - startTime
                    )
                )

                currentIds.add(nextTokenId)
                tokenIndex++

                inputs.values.forEach { it.close() }
                results.close()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Streaming inference error", e)
            close(e)
        } finally {
            isActive.set(false)
        }

        close()
        awaitClose { cancel() }
    }.flowOn(Dispatchers.Default)

    fun streamChunkedInference(
        inputData: FloatArray,
        chunkSize: Int,
        overlapSize: Int = 0
    ): Flow<StreamingChunk> = callbackFlow {
        isActive.set(true)
        val startTime = System.currentTimeMillis()

        try {
            val totalChunks = (inputData.size + chunkSize - 1) / chunkSize
            var chunkIndex = 0

            while (isActive.get() && isActive() && chunkIndex < totalChunks) {
                val start = (chunkIndex * chunkSize - if (chunkIndex > 0) overlapSize else 0)
                    .coerceAtLeast(0)
                val end = ((chunkIndex + 1) * chunkSize).coerceAtMost(inputData.size)
                val chunk = inputData.sliceArray(start until end)

                val inputTensor = OnnxTensor.createTensor(
                    ortEnvironment,
                    FloatBuffer.wrap(chunk),
                    longArrayOf(1, chunk.size.toLong())
                )

                val inputName = session.inputNames.first()
                val results = session.run(mapOf(inputName to inputTensor))
                val output = results[0].value as Array<FloatArray>

                trySend(
                    StreamingChunk(
                        probabilities = output[0],
                        isFirst = chunkIndex == 0,
                        isFinal = chunkIndex == totalChunks - 1,
                        chunkIndex = chunkIndex,
                        elapsedMs = System.currentTimeMillis() - startTime
                    )
                )

                inputTensor.close()
                results.close()
                chunkIndex++
            }
        } catch (e: Exception) {
            Log.e(TAG, "Chunked inference error", e)
            close(e)
        } finally {
            isActive.set(false)
        }

        close()
        awaitClose { cancel() }
    }.flowOn(Dispatchers.Default)

    fun cancel() {
        isActive.set(false)
        kvCache?.values?.forEach { it.close() }
        kvCache = null
    }

    private fun sampleToken(logits: FloatArray, temperature: Float, topK: Int): Int {
        if (temperature <= 0f) {
            return logits.indices.maxByOrNull { logits[it] } ?: 0
        }

        val scaled = FloatArray(logits.size) { logits[it] / temperature }

        val indexed = scaled.mapIndexed { i, v -> i to v }
            .sortedByDescending { it.second }
            .take(topK)

        val maxVal = indexed.first().second
        val exps = indexed.map { (i, v) -> i to Math.exp((v - maxVal).toDouble()).toFloat() }
        val sumExp = exps.sumOf { it.second.toDouble() }.toFloat()
        val probs = exps.map { (i, v) -> i to v / sumExp }

        var cumulative = 0f
        val random = Math.random().toFloat()
        for ((tokenId, prob) in probs) {
            cumulative += prob
            if (cumulative >= random) return tokenId
        }

        return probs.last().first
    }
}
