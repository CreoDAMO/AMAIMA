package com.amaima.app.ml

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.isActive
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.max

data class TranscriptionResult(
    val text: String,
    val language: String = "en",
    val confidence: Float = 0f,
    val segments: List<TranscriptionSegment> = emptyList(),
    val elapsedMs: Long = 0L
)

data class TranscriptionSegment(
    val text: String,
    val startMs: Long,
    val endMs: Long,
    val confidence: Float
)

data class AudioConfig(
    val sampleRate: Int = 16000,
    val channels: Int = 1,
    val chunkDurationMs: Int = 30000,
    val language: String = "en",
    val vadThreshold: Float = 0.01f
)

class AudioEngine(
    private val context: Context,
    private val ortEnvironment: OrtEnvironment
) {
    private var encoderSession: OrtSession? = null
    private var decoderSession: OrtSession? = null
    private var isRecording = AtomicBoolean(false)

    companion object {
        private const val TAG = "AudioEngine"
        private const val SAMPLE_RATE = 16000
        private const val N_FFT = 400
        private const val HOP_LENGTH = 160
        private const val N_MELS = 80
        private const val CHUNK_LENGTH_S = 30
        private const val N_SAMPLES = SAMPLE_RATE * CHUNK_LENGTH_S
    }

    suspend fun loadModel(
        encoderPath: String,
        decoderPath: String? = null
    ) = withContext(Dispatchers.IO) {
        try {
            val options = OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(4)
                setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            }
            encoderSession = ortEnvironment.createSession(encoderPath, options)

            decoderPath?.let {
                decoderSession = ortEnvironment.createSession(it, options)
            }

            Log.d(TAG, "Whisper model loaded")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load Whisper model", e)
        }
    }

    suspend fun transcribeFile(audioFile: File, config: AudioConfig = AudioConfig()): TranscriptionResult =
        withContext(Dispatchers.Default) {
            val startTime = System.currentTimeMillis()

            try {
                val rawAudio = loadAudioFile(audioFile, config.sampleRate)
                val chunks = splitIntoChunks(rawAudio, N_SAMPLES)
                val segments = mutableListOf<TranscriptionSegment>()
                val fullText = StringBuilder()

                chunks.forEachIndexed { index, chunk ->
                    val melSpectrogram = computeMelSpectrogram(chunk)
                    val transcription = runInference(melSpectrogram)

                    val startMs = (index * CHUNK_LENGTH_S * 1000L)
                    val endMs = ((index + 1) * CHUNK_LENGTH_S * 1000L)

                    if (transcription.isNotBlank()) {
                        segments.add(
                            TranscriptionSegment(
                                text = transcription.trim(),
                                startMs = startMs,
                                endMs = endMs,
                                confidence = 0.85f
                            )
                        )
                        if (fullText.isNotEmpty()) fullText.append(" ")
                        fullText.append(transcription.trim())
                    }
                }

                TranscriptionResult(
                    text = fullText.toString(),
                    language = config.language,
                    confidence = if (segments.isNotEmpty()) segments.map { it.confidence }.average().toFloat() else 0f,
                    segments = segments,
                    elapsedMs = System.currentTimeMillis() - startTime
                )
            } catch (e: Exception) {
                Log.e(TAG, "Transcription failed", e)
                TranscriptionResult(
                    text = "",
                    elapsedMs = System.currentTimeMillis() - startTime
                )
            }
        }

    fun streamTranscription(config: AudioConfig = AudioConfig()): Flow<TranscriptionSegment> = callbackFlow {
        isRecording.set(true)

        val bufferSize = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_FLOAT
        )

        val audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_FLOAT,
            bufferSize * 2
        )

        try {
            audioRecord.startRecording()
            val chunkSamples = config.chunkDurationMs * SAMPLE_RATE / 1000
            val audioBuffer = FloatArray(chunkSamples)
            var chunkIndex = 0
            var bufferOffset = 0

            val readBuffer = FloatArray(bufferSize)

            while (isRecording.get() && isActive) {
                val bytesRead = audioRecord.read(readBuffer, 0, readBuffer.size, AudioRecord.READ_BLOCKING)

                if (bytesRead > 0) {
                    val remaining = chunkSamples - bufferOffset
                    val toCopy = minOf(bytesRead, remaining)
                    System.arraycopy(readBuffer, 0, audioBuffer, bufferOffset, toCopy)
                    bufferOffset += toCopy

                    if (bufferOffset >= chunkSamples) {
                        if (detectVoiceActivity(audioBuffer, config.vadThreshold)) {
                            val padded = padOrTruncate(audioBuffer, N_SAMPLES)
                            val mel = computeMelSpectrogram(padded)
                            val text = runInference(mel)

                            if (text.isNotBlank()) {
                                trySend(
                                    TranscriptionSegment(
                                        text = text.trim(),
                                        startMs = (chunkIndex * config.chunkDurationMs).toLong(),
                                        endMs = ((chunkIndex + 1) * config.chunkDurationMs).toLong(),
                                        confidence = 0.8f
                                    )
                                )
                            }
                        }

                        bufferOffset = 0
                        chunkIndex++
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Streaming transcription error", e)
            close(e)
        } finally {
            audioRecord.stop()
            audioRecord.release()
            isRecording.set(false)
        }

        close()
        awaitClose { stopRecording() }
    }.flowOn(Dispatchers.IO)

    fun stopRecording() {
        isRecording.set(false)
    }

    fun isModelLoaded(): Boolean {
        return encoderSession != null
    }

    private fun runInference(melSpectrogram: FloatArray): String {
        val session = encoderSession ?: return ""

        val inputName = session.inputNames.first()
        val melFrames = melSpectrogram.size / N_MELS

        val inputTensor = OnnxTensor.createTensor(
            ortEnvironment,
            FloatBuffer.wrap(melSpectrogram),
            longArrayOf(1, N_MELS.toLong(), melFrames.toLong())
        )

        val results = session.run(mapOf(inputName to inputTensor))
        val output = results[0].value

        val text = when (output) {
            is Array<*> -> {
                @Suppress("UNCHECKED_CAST")
                val tokenIds = (output as? Array<IntArray>)?.firstOrNull()
                tokenIds?.joinToString("") { decodeToken(it) } ?: ""
            }
            is LongArray -> output.joinToString("") { decodeToken(it.toInt()) }
            else -> ""
        }

        inputTensor.close()
        results.close()

        return text
    }

    fun computeMelSpectrogram(audio: FloatArray): FloatArray {
        val numFrames = (audio.size - N_FFT) / HOP_LENGTH + 1
        val melSpec = FloatArray(N_MELS * numFrames)
        val window = hanningWindow(N_FFT)
        val melFilterbank = createMelFilterbank(N_FFT / 2 + 1, N_MELS, SAMPLE_RATE)

        for (frame in 0 until numFrames) {
            val start = frame * HOP_LENGTH
            val windowed = FloatArray(N_FFT) { i ->
                if (start + i < audio.size) audio[start + i] * window[i] else 0f
            }

            val fftMagnitude = computeFFTMagnitude(windowed)

            for (mel in 0 until N_MELS) {
                var sum = 0f
                for (bin in fftMagnitude.indices) {
                    sum += fftMagnitude[bin] * melFilterbank[mel * (N_FFT / 2 + 1) + bin]
                }
                melSpec[mel * numFrames + frame] = max(ln(max(sum, 1e-10f)), -10f)
            }
        }

        return melSpec
    }

    private fun hanningWindow(size: Int): FloatArray {
        return FloatArray(size) { i ->
            (0.5f * (1f - cos(2f * PI.toFloat() * i / (size - 1))))
        }
    }

    private fun computeFFTMagnitude(data: FloatArray): FloatArray {
        val n = data.size
        val magnitude = FloatArray(n / 2 + 1)
        for (k in magnitude.indices) {
            var real = 0f
            var imag = 0f
            for (t in 0 until n) {
                val angle = 2f * PI.toFloat() * k * t / n
                real += data[t] * cos(angle)
                imag -= data[t] * kotlin.math.sin(angle)
            }
            magnitude[k] = kotlin.math.sqrt(real * real + imag * imag)
        }
        return magnitude
    }

    private fun createMelFilterbank(numBins: Int, numMels: Int, sampleRate: Int): FloatArray {
        val filterbank = FloatArray(numMels * numBins)
        val fMin = 0f
        val fMax = sampleRate / 2f

        fun hzToMel(hz: Float) = 2595f * kotlin.math.log10(1f + hz / 700f)
        fun melToHz(mel: Float) = 700f * (kotlin.math.pow(10.0, (mel / 2595f).toDouble()).toFloat() - 1f)

        val melMin = hzToMel(fMin)
        val melMax = hzToMel(fMax)
        val melPoints = FloatArray(numMels + 2) { i ->
            melToHz(melMin + (melMax - melMin) * i / (numMels + 1))
        }

        val binPoints = FloatArray(numMels + 2) { i ->
            (melPoints[i] * numBins * 2 / sampleRate).toInt().toFloat()
        }

        for (m in 0 until numMels) {
            for (k in 0 until numBins) {
                val kf = k.toFloat()
                filterbank[m * numBins + k] = when {
                    kf < binPoints[m] -> 0f
                    kf <= binPoints[m + 1] -> (kf - binPoints[m]) / (binPoints[m + 1] - binPoints[m] + 1e-8f)
                    kf <= binPoints[m + 2] -> (binPoints[m + 2] - kf) / (binPoints[m + 2] - binPoints[m + 1] + 1e-8f)
                    else -> 0f
                }
            }
        }

        return filterbank
    }

    private fun detectVoiceActivity(audio: FloatArray, threshold: Float): Boolean {
        val energy = audio.sumOf { (it * it).toDouble() }.toFloat() / audio.size
        return energy > threshold
    }

    private fun loadAudioFile(file: File, targetSampleRate: Int): FloatArray {
        val bytes = file.readBytes()

        if (bytes.size > 44 && String(bytes.sliceArray(0..3)) == "RIFF") {
            val dataStart = 44
            val numSamples = (bytes.size - dataStart) / 2
            val buffer = ByteBuffer.wrap(bytes, dataStart, bytes.size - dataStart)
                .order(ByteOrder.LITTLE_ENDIAN)
            return FloatArray(numSamples) { buffer.short.toFloat() / 32768f }
        }

        return FloatArray(bytes.size / 4) {
            ByteBuffer.wrap(bytes, it * 4, 4)
                .order(ByteOrder.LITTLE_ENDIAN)
                .float
        }
    }

    private fun splitIntoChunks(audio: FloatArray, chunkSize: Int): List<FloatArray> {
        val chunks = mutableListOf<FloatArray>()
        var offset = 0
        while (offset < audio.size) {
            val end = minOf(offset + chunkSize, audio.size)
            val chunk = padOrTruncate(audio.sliceArray(offset until end), chunkSize)
            chunks.add(chunk)
            offset += chunkSize
        }
        return chunks
    }

    private fun padOrTruncate(audio: FloatArray, targetSize: Int): FloatArray {
        return when {
            audio.size == targetSize -> audio
            audio.size > targetSize -> audio.sliceArray(0 until targetSize)
            else -> FloatArray(targetSize).also { audio.copyInto(it) }
        }
    }

    private fun decodeToken(tokenId: Int): String {
        return when {
            tokenId in 0..255 -> tokenId.toChar().toString()
            tokenId == 50256 -> ""
            tokenId == 50257 -> ""
            else -> " "
        }
    }

    fun close() {
        stopRecording()
        encoderSession?.close()
        decoderSession?.close()
        encoderSession = null
        decoderSession = null
    }
}
