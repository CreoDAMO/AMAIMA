package com.amaima.app.data.websocket

import okhttp3.OkHttpClient
import com.amaima.app.security.EncryptedPreferences
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WebSocketManagerImpl @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val encryptedPrefs: EncryptedPreferences
) : WebSocketManager {
    override fun connect() {}
    override fun disconnect() {}
}
