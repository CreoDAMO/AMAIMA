package com.amaima.app.ml

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.nio.FloatBuffer
import kotlin.math.exp

data class ClassificationResult(
    val label: String,
    val confidence: Float,
    val index: Int,
    val topK: List<Pair<String, Float>> = emptyList(),
    val elapsedMs: Long = 0L
)

data class OcrResult(
    val text: String,
    val confidence: Float,
    val boundingBoxes: List<TextRegion> = emptyList(),
    val elapsedMs: Long = 0L
)

data class TextRegion(
    val text: String,
    val x: Float,
    val y: Float,
    val width: Float,
    val height: Float,
    val confidence: Float
)

data class ObjectDetection(
    val label: String,
    val confidence: Float,
    val x: Float,
    val y: Float,
    val width: Float,
    val height: Float
)

class VisionEngine(
    private val context: Context,
    private val ortEnvironment: OrtEnvironment
) {
    private var classificationSession: OrtSession? = null
    private var ocrSession: OrtSession? = null
    private var detectionSession: OrtSession? = null
    private var classificationLabels: List<String> = emptyList()

    companion object {
        private const val TAG = "VisionEngine"
        private const val CLASSIFICATION_SIZE = 224
        private const val OCR_HEIGHT = 32
        private const val OCR_WIDTH = 320
        private const val DETECTION_SIZE = 640
    }

    suspend fun loadClassificationModel(
        modelPath: String,
        labels: List<String> = emptyList()
    ) = withContext(Dispatchers.IO) {
        try {
            val options = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }
            classificationSession = ortEnvironment.createSession(modelPath, options)
            classificationLabels = labels.ifEmpty { loadDefaultLabels() }
            Log.d(TAG, "Classification model loaded with ${classificationLabels.size} labels")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load classification model", e)
        }
    }

    suspend fun loadOcrModel(modelPath: String) = withContext(Dispatchers.IO) {
        try {
            val options = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }
            ocrSession = ortEnvironment.createSession(modelPath, options)
            Log.d(TAG, "OCR model loaded")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load OCR model", e)
        }
    }

    suspend fun loadDetectionModel(modelPath: String) = withContext(Dispatchers.IO) {
        try {
            val options = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }
            detectionSession = ortEnvironment.createSession(modelPath, options)
            Log.d(TAG, "Object detection model loaded")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load detection model", e)
        }
    }

    suspend fun classifyImage(
        bitmap: Bitmap,
        topK: Int = 5
    ): ClassificationResult = withContext(Dispatchers.Default) {
        val startTime = System.currentTimeMillis()
        val session = classificationSession
            ?: throw IllegalStateException("Classification model not loaded")

        val resized = Bitmap.createScaledBitmap(bitmap, CLASSIFICATION_SIZE, CLASSIFICATION_SIZE, true)
        val pixels = preprocessForClassification(resized)
        val inputName = session.inputNames.first()

        val inputTensor = OnnxTensor.createTensor(
            ortEnvironment,
            FloatBuffer.wrap(pixels),
            longArrayOf(1, 3, CLASSIFICATION_SIZE.toLong(), CLASSIFICATION_SIZE.toLong())
        )

        val results = session.run(mapOf(inputName to inputTensor))
        val logits = results[0].value as Array<FloatArray>
        val probabilities = softmax(logits[0])

        val topKResults = probabilities.indices
            .sortedByDescending { probabilities[it] }
            .take(topK)
            .map { idx ->
                val label = if (idx < classificationLabels.size) classificationLabels[idx] else "class_$idx"
                label to probabilities[idx]
            }

        inputTensor.close()
        results.close()

        val bestIdx = topKResults.firstOrNull()?.let { (label, _) ->
            classificationLabels.indexOf(label).takeIf { it >= 0 } ?: 0
        } ?: 0

        ClassificationResult(
            label = topKResults.firstOrNull()?.first ?: "unknown",
            confidence = topKResults.firstOrNull()?.second ?: 0f,
            index = bestIdx,
            topK = topKResults,
            elapsedMs = System.currentTimeMillis() - startTime
        )
    }

    suspend fun classifyImageFile(file: File, topK: Int = 5): ClassificationResult {
        val bitmap = BitmapFactory.decodeFile(file.absolutePath)
            ?: throw IllegalArgumentException("Could not decode image: ${file.path}")
        return classifyImage(bitmap, topK)
    }

    suspend fun recognizeText(bitmap: Bitmap): OcrResult = withContext(Dispatchers.Default) {
        val startTime = System.currentTimeMillis()
        val session = ocrSession
            ?: throw IllegalStateException("OCR model not loaded")

        val resized = Bitmap.createScaledBitmap(bitmap, OCR_WIDTH, OCR_HEIGHT, true)
        val pixels = preprocessForOcr(resized)
        val inputName = session.inputNames.first()

        val inputTensor = OnnxTensor.createTensor(
            ortEnvironment,
            FloatBuffer.wrap(pixels),
            longArrayOf(1, 1, OCR_HEIGHT.toLong(), OCR_WIDTH.toLong())
        )

        val results = session.run(mapOf(inputName to inputTensor))
        val output = results[0].value

        val text = decodeOcrOutput(output)

        inputTensor.close()
        results.close()

        OcrResult(
            text = text,
            confidence = 0.85f,
            elapsedMs = System.currentTimeMillis() - startTime
        )
    }

    suspend fun recognizeTextFromFile(file: File): OcrResult {
        val bitmap = BitmapFactory.decodeFile(file.absolutePath)
            ?: throw IllegalArgumentException("Could not decode image: ${file.path}")
        return recognizeText(bitmap)
    }

    suspend fun detectObjects(
        bitmap: Bitmap,
        confidenceThreshold: Float = 0.5f
    ): List<ObjectDetection> = withContext(Dispatchers.Default) {
        val session = detectionSession
            ?: throw IllegalStateException("Detection model not loaded")

        val resized = Bitmap.createScaledBitmap(bitmap, DETECTION_SIZE, DETECTION_SIZE, true)
        val pixels = preprocessForClassification(resized)
        val inputName = session.inputNames.first()

        val inputTensor = OnnxTensor.createTensor(
            ortEnvironment,
            FloatBuffer.wrap(pixels),
            longArrayOf(1, 3, DETECTION_SIZE.toLong(), DETECTION_SIZE.toLong())
        )

        val results = session.run(mapOf(inputName to inputTensor))
        val output = results[0].value as Array<Array<FloatArray>>

        val detections = mutableListOf<ObjectDetection>()
        val boxes = output[0]

        for (box in boxes) {
            if (box.size < 6) continue
            val confidence = box[4]
            if (confidence < confidenceThreshold) continue

            val classScores = box.drop(5)
            val classIdx = classScores.indices.maxByOrNull { classScores[it] } ?: continue
            val classConfidence = classScores[classIdx] * confidence

            if (classConfidence >= confidenceThreshold) {
                val label = if (classIdx < classificationLabels.size) classificationLabels[classIdx] else "object_$classIdx"
                detections.add(
                    ObjectDetection(
                        label = label,
                        confidence = classConfidence,
                        x = box[0] / DETECTION_SIZE,
                        y = box[1] / DETECTION_SIZE,
                        width = box[2] / DETECTION_SIZE,
                        height = box[3] / DETECTION_SIZE
                    )
                )
            }
        }

        inputTensor.close()
        results.close()

        detections.sortedByDescending { it.confidence }
    }

    private fun preprocessForClassification(bitmap: Bitmap): FloatArray {
        val width = bitmap.width
        val height = bitmap.height
        val pixels = IntArray(width * height)
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height)

        val floats = FloatArray(3 * width * height)
        val mean = floatArrayOf(0.485f, 0.456f, 0.406f)
        val std = floatArrayOf(0.229f, 0.224f, 0.225f)

        for (i in pixels.indices) {
            val pixel = pixels[i]
            floats[i] = ((Color.red(pixel) / 255f) - mean[0]) / std[0]
            floats[width * height + i] = ((Color.green(pixel) / 255f) - mean[1]) / std[1]
            floats[2 * width * height + i] = ((Color.blue(pixel) / 255f) - mean[2]) / std[2]
        }
        return floats
    }

    private fun preprocessForOcr(bitmap: Bitmap): FloatArray {
        val width = bitmap.width
        val height = bitmap.height
        val pixels = IntArray(width * height)
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height)

        return FloatArray(width * height) { i ->
            val pixel = pixels[i]
            val gray = (Color.red(pixel) * 0.299f + Color.green(pixel) * 0.587f + Color.blue(pixel) * 0.114f) / 255f
            (gray - 0.5f) / 0.5f
        }
    }

    private fun softmax(logits: FloatArray): FloatArray {
        val maxVal = logits.max()
        val exps = FloatArray(logits.size) { exp(logits[it] - maxVal) }
        val sumExp = exps.sum()
        return FloatArray(logits.size) { exps[it] / sumExp }
    }

    private fun decodeOcrOutput(output: Any): String {
        return when (output) {
            is Array<*> -> {
                @Suppress("UNCHECKED_CAST")
                val indices = (output as? Array<Array<FloatArray>>)?.firstOrNull()
                indices?.let { frames ->
                    val chars = mutableListOf<Int>()
                    var prevIdx = -1
                    for (frame in frames) {
                        val idx = frame.indices.maxByOrNull { frame[it] } ?: continue
                        if (idx != 0 && idx != prevIdx) {
                            chars.add(idx)
                        }
                        prevIdx = idx
                    }
                    chars.joinToString("") { (it + 31).toChar().toString() }
                } ?: ""
            }
            else -> ""
        }
    }

    private fun loadDefaultLabels(): List<String> {
        return listOf(
            "background", "person", "bicycle", "car", "motorcycle", "airplane", "bus",
            "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign",
            "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
            "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag",
            "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
            "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
            "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza",
            "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table",
            "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
            "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock",
            "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
        )
    }

    fun close() {
        classificationSession?.close()
        ocrSession?.close()
        detectionSession?.close()
        classificationSession = null
        ocrSession = null
        detectionSession = null
    }
}
