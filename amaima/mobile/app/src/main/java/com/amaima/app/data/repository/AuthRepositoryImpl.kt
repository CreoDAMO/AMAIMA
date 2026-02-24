package com.amaima.app.data.repository

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor() : AuthRepository {
    override suspend fun login(credentials: Any): Any = Unit
    override suspend fun logout(): Unit = Unit
}
