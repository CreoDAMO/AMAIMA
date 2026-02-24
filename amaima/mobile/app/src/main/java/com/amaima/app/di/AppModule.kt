package com.amaima.app.di

import android.content.Context
import androidx.room.Room
import com.amaima.app.BuildConfig
import com.amaima.app.data.local.entity.AmaimaDatabase
import com.amaima.app.data.local.entity.QueryDao
import com.amaima.app.data.local.entity.WorkflowDao
import com.amaima.app.data.local.entity.UserDao
import com.amaima.app.data.repository.AuthRepository
import com.amaima.app.data.repository.AuthRepositoryImpl
import com.amaima.app.data.repository.QueryRepository
import com.amaima.app.data.local.entity.QueryRepositoryImpl
import com.amaima.app.data.websocket.WebSocketManager
import com.amaima.app.data.websocket.WebSocketManagerImpl
import com.amaima.app.data.remote.api.AmaimaApi
import com.amaima.app.data.remote.websocket.AmaimaWebSocket
import com.amaima.app.data.remote.interceptor.AuthInterceptor
import com.amaima.app.security.EncryptedPreferences
import com.amaima.app.util.NetworkMonitor
import com.amaima.app.ml.*
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds
    @Singleton
    abstract fun bindAuthRepository(impl: AuthRepositoryImpl): AuthRepository

    @Binds
    @Singleton
    abstract fun bindQueryRepository(impl: QueryRepositoryImpl): QueryRepository
}

@Module
@InstallIn(SingletonComponent::class)
abstract class ServiceModule {
    @Binds
    @Singleton
    abstract fun bindWebSocketManager(impl: WebSocketManagerImpl): WebSocketManager
}

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    @Singleton
    fun provideContext(@ApplicationContext context: Context): Context = context

    @Provides
    @Singleton
    fun provideNetworkMonitor(@ApplicationContext context: Context): NetworkMonitor = NetworkMonitor(context)

    @Provides
    @Singleton
    fun provideEncryptedPreferences(@ApplicationContext context: Context): EncryptedPreferences = EncryptedPreferences(context)
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideOkHttpClient(authInterceptor: AuthInterceptor): OkHttpClient {
        return OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient, moshi: Moshi): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://api.example.com")
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
    }

    @Provides
    @Singleton
    fun provideAmaimaApi(retrofit: Retrofit): AmaimaApi = retrofit.create(AmaimaApi::class.java)

    @Provides
    @Singleton
    fun provideMoshi(): Moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
}

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AmaimaDatabase {
        return Room.databaseBuilder(context, AmaimaDatabase::class.java, "amaima.db").build()
    }

    @Provides
    fun provideQueryDao(db: AmaimaDatabase): QueryDao = db.queryDao()

    @Provides
    fun provideWorkflowDao(db: AmaimaDatabase): WorkflowDao = db.workflowDao()

    @Provides
    fun provideUserDao(db: AmaimaDatabase): UserDao = db.userDao()
}
