package com.amaima.app.data.websocket

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WebSocketManagerImpl @Inject constructor() : WebSocketManager {
    override fun connect(): Unit = Unit
    override fun disconnect(): Unit = Unit
}
