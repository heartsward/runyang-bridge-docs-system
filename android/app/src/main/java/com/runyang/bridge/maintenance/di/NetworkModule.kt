package com.runyang.bridge.maintenance.di

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.runyang.bridge.maintenance.BuildConfig
import com.runyang.bridge.maintenance.data.remote.api.ApiService
import com.runyang.bridge.maintenance.data.remote.interceptor.AuthInterceptor
import com.runyang.bridge.maintenance.data.remote.interceptor.NetworkInterceptor
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

/**
 * 网络模块 - 提供网络请求相关依赖
 */
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    /**
     * 提供Gson实例
     */
    @Provides
    @Singleton
    fun provideGson(): Gson = GsonBuilder()
        .setLenient()
        .serializeNulls()
        .setDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'")
        .create()

    /**
     * 提供Kotlinx Serialization Json实例
     */
    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
        useAlternativeNames = true
    }

    /**
     * 提供HTTP日志拦截器
     */
    @Provides
    @Singleton
    fun provideHttpLoggingInterceptor(): HttpLoggingInterceptor {
        val logging = HttpLoggingInterceptor { message ->
            if (BuildConfig.DEBUG_MODE) {
                println("HTTP: $message")
            }
        }
        logging.setLevel(
            if (BuildConfig.DEBUG_MODE) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        )
        return logging
    }

    /**
     * 提供OkHttpClient
     */
    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        networkInterceptor: NetworkInterceptor,
        loggingInterceptor: HttpLoggingInterceptor
    ): OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .callTimeout(90, TimeUnit.SECONDS)
        .retryOnConnectionFailure(true)
        .addInterceptor(networkInterceptor)
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .build()

    /**
     * 提供Retrofit实例
     */
    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        gson: Gson,
        json: Json
    ): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .addConverterFactory(GsonConverterFactory.create(gson))
        .build()

    /**
     * 提供API服务
     */
    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService = 
        retrofit.create(ApiService::class.java)
}