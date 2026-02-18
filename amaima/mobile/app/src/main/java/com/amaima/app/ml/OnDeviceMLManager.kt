package com.amaima.app.ml

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import java.io.File
import java.nio.FloatBuffer
import java.util.concurrent.ConcurrentHashMap

class OnDeviceMLManager(
    private val context: Context,
    private val modelDownloader: ModelDownloader
) {
    val ortEnvironment: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val onnxSessions = ConcurrentHashMap<String, OrtSession>()
    private val tfliteInterpreters = ConcurrentHashMap<String, Interpreter>()
    private val models = ConcurrentHashMap<String, MLModel>()

    val registry = ModelRegistry()
    val modelStore = ModelStore(context, modelDownloader)
    val embeddingEngine = EmbeddingEngine(context, ortEnvironment)
    val audioEngine = AudioEngine(context, ortEnvironment)
    val visionEngine = VisionEngine(context, ortEnvironment)

    companion object {
        private const val TAG = "OnDeviceMLManager"
        private const val MODEL_CACHE_SIZE = 500L * 1024 * 1024
        private const val MODEL_VERSION = "1.0.0"
    }

    enum class Runtime { ONNX, TFLITE }

    data class MLModel(
        val name: String,
        val version: String,
        val modelPath: String,
        val runtime: Runtime,
        val precision: ModelPrecision = ModelPrecision.FP32,
        val inputShape: IntArray,
        val outputShape: IntArray,
        val labels: List<String>
    ) {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            other as MLModel
            return name == other.name && version == other.version
        }

        override fun hashCode(): Int {
            var result = name.hashCode()
            result = 31 * result + version.hashCode()
            return result
        }
    }

    suspend fun loadDefaultModels() {
        val defaultModels = listOf(
            MLModel(
                name = "complexity_estimator",
                version = MODEL_VERSION,
                modelPath = "models/complexity_estimator.onnx",
                runtime = Runtime.ONNX,
                inputShape = intArrayOf(1, 128),
                outputShape = intArrayOf(1, 5),
                labels = listOf("TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "EXPERT")
            ),
            MLModel(
                name = "keyword_extractor",
                version = MODEL_VERSION,
                modelPath = "models/keyword_extractor.onnx",
                runtime = Runtime.ONNX,
                inputShape = intArrayOf(1, 64),
                outputShape = intArrayOf(1, 10),
                labels = emptyList()
            ),
            MLModel(
                name = "sentiment_analyzer",
                version = MODEL_VERSION,
                modelPath = "models/sentiment_analyzer.tflite",
                runtime = Runtime.TFLITE,
                inputShape = intArrayOf(1, 128),
                outputShape = intArrayOf(1, 3),
                labels = listOf("NEGATIVE", "NEUTRAL", "POSITIVE")
            )
        )

        defaultModels.forEach { model ->
            registry.register(model.toMetadata())
            loadModel(model)
        }
    }

    suspend fun loadModel(model: MLModel) {
        withContext(Dispatchers.IO) {
            try {
                registry.updateState(model.name, model.precision, ModelState.LOADING)

                val metadata = model.toMetadata()
                registry.updateState(model.name, model.precision, ModelState.DOWNLOADING)

                val modelFile = modelStore.ensureModelAvailable(metadata) { progress ->
                    Log.d(TAG, "Download progress for ${model.name}: ${(progress * 100).toInt()}%")
                }

                if (modelFile == null) {
                    registry.updateState(model.name, model.precision, ModelState.ERROR, error = "Download failed or checksum mismatch")
                    Log.w(TAG, "Failed to obtain model via ModelStore: ${model.name}")
                    return@withContext
                }

                when (model.runtime) {
                    Runtime.ONNX -> loadOnnxModel(model, modelFile)
                    Runtime.TFLITE -> loadTfliteModel(model, modelFile)
                }

                models[model.name] = model
                registry.updateState(
                    model.name, model.precision, ModelState.LOADED,
                    memorySizeBytes = modelFile.length()
                )
                Log.d(TAG, "Model loaded (${model.runtime}): ${model.name}")
            } catch (e: Exception) {
                registry.updateState(model.name, model.precision, ModelState.ERROR, error = e.message)
                Log.e(TAG, "Failed to load model: ${model.name}", e)
            }
        }
    }

    suspend fun hotSwapModel(
        modelName: String,
        newModelPath: String,
        newVersion: String,
        newPrecision: ModelPrecision = ModelPrecision.FP32
    ) {
        withContext(Dispatchers.IO) {
            val existing = models[modelName]
            if (existing != null) {
                Log.d(TAG, "Hot-swapping model: $modelName (${existing.version} -> $newVersion)")
                unloadModel(modelName)
            }

            val newModel = existing?.copy(
                modelPath = newModelPath,
                version = newVersion,
                precision = newPrecision
            ) ?: return@withContext

            loadModel(newModel)
            Log.d(TAG, "Hot-swap complete: $modelName v$newVersion (${newPrecision.label})")
        }
    }

    suspend fun switchPrecision(modelName: String, precision: ModelPrecision) {
        val model = models[modelName] ?: return

        val precisionPath = when (precision) {
            ModelPrecision.FP32 -> model.modelPath
            ModelPrecision.FP16 -> model.modelPath.replace(".onnx", "_fp16.onnx")
                .replace(".tflite", "_fp16.tflite")
            ModelPrecision.INT8 -> model.modelPath.replace(".onnx", "_int8.onnx")
                .replace(".tflite", "_int8.tflite")
            ModelPrecision.INT4 -> model.modelPath.replace(".onnx", "_int4.onnx")
                .replace(".tflite", "_int4.tflite")
        }

        hotSwapModel(modelName, precisionPath, model.version, precision)
    }

    fun createStreamingSession(
        modelName: String,
        config: StreamingConfig = StreamingConfig()
    ): StreamingSession? {
        val session = onnxSessions[modelName] ?: return null
        return StreamingSession(ortEnvironment, session, config)
    }

    fun streamInference(
        modelName: String,
        inputIds: IntArray,
        config: StreamingConfig = StreamingConfig()
    ): Flow<StreamingChunk>? {
        val session = createStreamingSession(modelName, config) ?: return null
        return session.streamInference(inputIds)
    }

    suspend fun generateEmbedding(text: String): EmbeddingResult {
        return embeddingEngine.embedText(text)
    }

    suspend fun generateImageEmbedding(bitmap: Bitmap): EmbeddingResult {
        return embeddingEngine.embedImage(bitmap)
    }

    suspend fun transcribeAudio(audioFile: File, config: AudioConfig = AudioConfig()): TranscriptionResult {
        return audioEngine.transcribeFile(audioFile, config)
    }

    fun streamTranscription(config: AudioConfig = AudioConfig()): Flow<TranscriptionSegment> {
        return audioEngine.streamTranscription(config)
    }

    suspend fun classifyImage(bitmap: Bitmap, topK: Int = 5): ClassificationResult {
        return visionEngine.classifyImage(bitmap, topK)
    }

    suspend fun recognizeText(bitmap: Bitmap): OcrResult {
        return visionEngine.recognizeText(bitmap)
    }

    private fun loadOnnxModel(model: MLModel, modelFile: File) {
        val sessionOptions = OrtSession.SessionOptions().apply {
            setIntraOpNumThreads(4)
            setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)

            when (model.precision) {
                ModelPrecision.FP16 -> {
                    try { addConfigEntry("session.graph_optimization_level", "99") } catch (_: Exception) {}
                }
                ModelPrecision.INT8 -> {
                    try { addConfigEntry("session.graph_optimization_level", "99") } catch (_: Exception) {}
                }
                else -> {}
            }
        }
        val session = ortEnvironment.createSession(modelFile.absolutePath, sessionOptions)
        onnxSessions[model.name] = session
    }

    private fun loadTfliteModel(model: MLModel, modelFile: File) {
        val options = Interpreter.Options().apply {
            setNumThreads(4)
            if (model.precision == ModelPrecision.FP16) {
                setUseNNAPI(true)
            }
        }
        val interpreter = Interpreter(modelFile, options)
        tfliteInterpreters[model.name] = interpreter
    }

    fun estimateComplexity(query: String): ComplexityResult {
        val model = models["complexity_estimator"]
            ?: return ComplexityResult("MODERATE", 0.5f, "default")

        return try {
            val input = preprocessQuery(query, 128)
            val probabilities = when (model.runtime) {
                Runtime.ONNX -> runOnnxInference("complexity_estimator", input, 5)
                Runtime.TFLITE -> runTfliteInference("complexity_estimator", input, 5)
            }

            val maxIndex = probabilities.indices.maxByOrNull { probabilities[it] } ?: 2
            val complexity = when (maxIndex) {
                0 -> "TRIVIAL"
                1 -> "SIMPLE"
                2 -> "MODERATE"
                3 -> "COMPLEX"
                4 -> "EXPERT"
                else -> "MODERATE"
            }

            ComplexityResult(complexity, probabilities[maxIndex], "ml_model")
        } catch (e: Exception) {
            Log.e(TAG, "Complexity estimation failed", e)
            ComplexityResult("MODERATE", 0.5f, "fallback")
        }
    }

    fun analyzeSentiment(text: String): SentimentResult {
        val model = models["sentiment_analyzer"]
            ?: return SentimentResult("NEUTRAL", 0.5f)

        return try {
            val input = preprocessQuery(text, 128)
            val probabilities = when (model.runtime) {
                Runtime.ONNX -> runOnnxInference("sentiment_analyzer", input, 3)
                Runtime.TFLITE -> runTfliteInference("sentiment_analyzer", input, 3)
            }

            val maxIndex = probabilities.indices.maxByOrNull { probabilities[it] } ?: 1
            val sentiment = when (maxIndex) {
                0 -> "NEGATIVE"
                1 -> "NEUTRAL"
                2 -> "POSITIVE"
                else -> "NEUTRAL"
            }

            SentimentResult(sentiment, probabilities[maxIndex])
        } catch (e: Exception) {
            Log.e(TAG, "Sentiment analysis failed", e)
            SentimentResult("NEUTRAL", 0.5f)
        }
    }

    fun runOnnxInference(modelName: String, input: FloatArray, outputSize: Int): FloatArray {
        val session = onnxSessions[modelName]
            ?: throw IllegalStateException("ONNX session not loaded: $modelName")

        val inputName = session.inputNames.first()

        val inputTensor = OnnxTensor.createTensor(
            ortEnvironment,
            FloatBuffer.wrap(input),
            longArrayOf(1, input.size.toLong())
        )

        val results = session.run(mapOf(inputName to inputTensor))
        val outputTensor = results[0].value as Array<FloatArray>
        inputTensor.close()
        results.close()

        return outputTensor[0]
    }

    fun runTfliteInference(modelName: String, input: FloatArray, outputSize: Int): FloatArray {
        val interpreter = tfliteInterpreters[modelName]
            ?: throw IllegalStateException("TFLite interpreter not loaded: $modelName")

        val inputArray = arrayOf(input)
        val output = Array(1) { FloatArray(outputSize) }
        interpreter.run(inputArray, output)
        return output[0]
    }

    private fun preprocessQuery(query: String, vectorSize: Int): FloatArray {
        val tokens = query.lowercase()
            .replace(Regex("[^a-z0-9\\s]"), "")
            .split("\\s+")
            .take(vectorSize)

        val vector = FloatArray(vectorSize) { 0f }
        tokens.forEachIndexed { index, token ->
            vector[index] = token.hashCode().toFloat() / Float.MAX_VALUE
        }

        return vector
    }

    fun getLoadedModels(): List<String> {
        return models.keys.toList()
    }

    fun isModelLoaded(modelName: String): Boolean {
        return models.containsKey(modelName)
    }

    fun getModelRuntime(modelName: String): Runtime? {
        return models[modelName]?.runtime
    }

    fun getModelPrecision(modelName: String): ModelPrecision {
        return models[modelName]?.precision ?: ModelPrecision.FP32
    }

    suspend fun unloadModel(modelName: String) {
        withContext(Dispatchers.IO) {
            onnxSessions.remove(modelName)?.close()
            tfliteInterpreters.remove(modelName)?.close()
            val model = models.remove(modelName)
            model?.let {
                registry.updateState(it.name, it.precision, ModelState.NOT_DOWNLOADED)
            }
            Log.d(TAG, "Model unloaded: $modelName")
        }
    }

    fun clearAllModels() {
        onnxSessions.values.forEach { it.close() }
        onnxSessions.clear()
        tfliteInterpreters.values.forEach { it.close() }
        tfliteInterpreters.clear()
        models.clear()
    }

    fun destroy() {
        clearAllModels()
        embeddingEngine.close()
        audioEngine.close()
        visionEngine.close()
        ortEnvironment.close()
    }

    private fun MLModel.toMetadata(): ModelMetadata {
        return ModelMetadata(
            name = name,
            version = version,
            modelPath = modelPath,
            runtime = runtime,
            precision = precision,
            inputShape = inputShape,
            outputShape = outputShape,
            labels = labels
        )
    }

    data class ComplexityResult(
        val complexity: String,
        val confidence: Float,
        val method: String
    )

    data class SentimentResult(
        val sentiment: String,
        val confidence: Float
    )
}
