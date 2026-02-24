package com.amaima.app.di

import android.content.Context
import androidx.room.Room
import com.amaima.app.BuildConfig
import com.amaima.app.data.local.AmaimaDatabase
import com.amaima.app.data.local.QueryDao
import com.amaima.app.data.local.WorkflowDao
import com.amaima.app.data.repository.AuthRepository
import com.amaima.app.data.repository.AuthRepositoryImpl
import com.amaima.app.data.repository.QueryRepository
import com.amaima.app.data.repository.QueryRepositoryImpl
import com.amaima.app.network.WebSocketManager
import com.amaima.app.network.WebSocketManagerImpl
import com.amaima.app.data.local.UserDao
import com.amaima.app.data.remote.AmaimaApi
import com.amaima.app.data.remote.AmaimaWebSocket
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
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
    fun provideContext(@ApplicationContext context: Context): Context {
        return context.applicationContext
    }

    @Provides
    @Singleton
    fun provideNetworkMonitor(@ApplicationContext context: Context): NetworkMonitor {
        return NetworkMonitor(context)
    }

    @Provides
    @Singleton
    fun provideEncryptedPreferences(
        @ApplicationContext context: Context
    ): EncryptedPreferences {
        return EncryptedPreferences(context)
    }
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        certificatePinning: CertificatePinning
    ): OkHttpClient {
        return OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) {
                    HttpLoggingInterceptor.Level.BODY
                } else {
                    HttpLoggingInterceptor.Level.NONE
                }
            })
            .certificatePinner(certificatePinning.getCertificatePinner())
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .pingInterval(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        moshi: Moshi
    ): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
    }

    @Provides
    @Singleton
    fun provideAmaimaApi(retrofit: Retrofit): AmaimaApi {
        return retrofit.create(AmaimaApi::class.java)
    }

    @Provides
    @Singleton
    fun provideWebSocketClient(
        okHttpClient: OkHttpClient
    ): AmaimaWebSocket {
        return AmaimaWebSocket(okHttpClient)
    }

    @Provides
    @Singleton
    fun provideMoshi(): Moshi {
        return Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()
    }
}

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context
    ): AmaimaDatabase {
        return Room.databaseBuilder(
            context,
            AmaimaDatabase::class.java,
            "amaima_database"
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    fun provideQueryDao(database: AmaimaDatabase): QueryDao {
        return database.queryDao()
    }

    @Provides
    fun provideWorkflowDao(database: AmaimaDatabase): WorkflowDao {
        return database.workflowDao()
    }

    @Provides
    fun provideUserDao(database: AmaimaDatabase): UserDao {
        return database.userDao()
    }
}

@Module
@InstallIn(SingletonComponent::class)
object MLModule {

    @Provides
    @Singleton
    fun provideModelDownloader(
        @ApplicationContext context: Context,
        okHttpClient: OkHttpClient
    ): ModelDownloader {
        return ModelDownloader(context, okHttpClient)
    }

    @Provides
    @Singleton
    fun provideOnDeviceMLManager(
        @ApplicationContext context: Context,
        modelDownloader: ModelDownloader
    ): OnDeviceMLManager {
        return OnDeviceMLManager(context, modelDownloader)
    }

    @Provides
    @Singleton
    fun provideModelRegistry(mlManager: OnDeviceMLManager): ModelRegistry {
        return mlManager.registry
    }

    @Provides
    @Singleton
    fun provideModelStore(mlManager: OnDeviceMLManager): ModelStore {
        return mlManager.modelStore
    }

    @Provides
    @Singleton
    fun provideEmbeddingEngine(mlManager: OnDeviceMLManager): EmbeddingEngine {
        return mlManager.embeddingEngine
    }

    @Provides
    @Singleton
    fun provideAudioEngine(mlManager: OnDeviceMLManager): AudioEngine {
        return mlManager.audioEngine
    }

    @Provides
    @Singleton
    fun provideVisionEngine(mlManager: OnDeviceMLManager): VisionEngine {
        return mlManager.visionEngine
    }

    @Provides
    @Singleton
    fun provideVectorStore(
        @ApplicationContext context: Context
    ): VectorStore {
        val persistFile = java.io.File(context.filesDir, "vector_store.bin")
        return VectorStore(
            dimensions = 384,
            maxEntries = 10000,
            persistFile = persistFile
        )
    }
}
