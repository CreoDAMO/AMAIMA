package com.amaima.app.ml

import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.ConcurrentHashMap

data class ModelMetadata(
    val name: String,
    val version: String,
    val modelPath: String,
    val runtime: OnDeviceMLManager.Runtime,
    val precision: ModelPrecision = ModelPrecision.FP32,
    val category: ModelCategory = ModelCategory.GENERAL,
    val inputShape: IntArray = intArrayOf(),
    val outputShape: IntArray = intArrayOf(),
    val labels: List<String> = emptyList(),
    val sizeBytes: Long = 0L,
    val description: String = "",
    val downloadUrl: String = ""
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as ModelMetadata
        return name == other.name && version == other.version && precision == other.precision
    }

    override fun hashCode(): Int {
        var result = name.hashCode()
        result = 31 * result + version.hashCode()
        result = 31 * result + precision.hashCode()
        return result
    }
}

enum class ModelPrecision(val label: String) {
    FP32("Float32"),
    FP16("Float16"),
    INT8("Int8"),
    INT4("Int4")
}

enum class ModelCategory {
    GENERAL,
    EMBEDDING,
    AUDIO,
    VISION,
    OCR,
    LANGUAGE
}

enum class ModelState {
    NOT_DOWNLOADED,
    DOWNLOADING,
    DOWNLOADED,
    LOADING,
    LOADED,
    UNLOADING,
    ERROR
}

data class ModelInfo(
    val metadata: ModelMetadata,
    val state: ModelState = ModelState.NOT_DOWNLOADED,
    val downloadProgress: Float = 0f,
    val errorMessage: String? = null,
    val loadedAtMs: Long = 0L,
    val memorySizeBytes: Long = 0L
)

class ModelRegistry {

    private val _registeredModels = ConcurrentHashMap<String, ModelInfo>()
    private val _modelsFlow = MutableStateFlow<Map<String, ModelInfo>>(emptyMap())
    val modelsFlow: StateFlow<Map<String, ModelInfo>> = _modelsFlow.asStateFlow()

    companion object {
        private const val TAG = "ModelRegistry"
    }

    fun register(metadata: ModelMetadata) {
        val key = modelKey(metadata.name, metadata.precision)
        _registeredModels[key] = ModelInfo(metadata = metadata)
        emitUpdate()
        Log.d(TAG, "Registered model: $key")
    }

    fun registerAll(models: List<ModelMetadata>) {
        models.forEach { register(it) }
    }

    fun unregister(name: String, precision: ModelPrecision = ModelPrecision.FP32) {
        val key = modelKey(name, precision)
        _registeredModels.remove(key)
        emitUpdate()
        Log.d(TAG, "Unregistered model: $key")
    }

    fun getModel(name: String, precision: ModelPrecision = ModelPrecision.FP32): ModelInfo? {
        return _registeredModels[modelKey(name, precision)]
    }

    fun getModelsByCategory(category: ModelCategory): List<ModelInfo> {
        return _registeredModels.values.filter { it.metadata.category == category }
    }

    fun getLoadedModels(): List<ModelInfo> {
        return _registeredModels.values.filter { it.state == ModelState.LOADED }
    }

    fun getAllModels(): List<ModelInfo> {
        return _registeredModels.values.toList()
    }

    fun updateState(
        name: String,
        precision: ModelPrecision = ModelPrecision.FP32,
        state: ModelState,
        progress: Float = 0f,
        error: String? = null,
        memorySizeBytes: Long = 0L
    ) {
        val key = modelKey(name, precision)
        _registeredModels[key]?.let { info ->
            _registeredModels[key] = info.copy(
                state = state,
                downloadProgress = progress,
                errorMessage = error,
                loadedAtMs = if (state == ModelState.LOADED) System.currentTimeMillis() else info.loadedAtMs,
                memorySizeBytes = memorySizeBytes
            )
            emitUpdate()
        }
    }

    fun getAvailableVariants(name: String): List<ModelInfo> {
        return _registeredModels.values.filter { it.metadata.name == name }
    }

    fun isLoaded(name: String, precision: ModelPrecision = ModelPrecision.FP32): Boolean {
        return getModel(name, precision)?.state == ModelState.LOADED
    }

    private fun modelKey(name: String, precision: ModelPrecision): String {
        return if (precision == ModelPrecision.FP32) name else "${name}_${precision.name.lowercase()}"
    }

    private fun emitUpdate() {
        _modelsFlow.value = _registeredModels.toMap()
    }
}
