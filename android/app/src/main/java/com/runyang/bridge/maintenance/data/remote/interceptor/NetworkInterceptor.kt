package com.runyang.bridge.maintenance.data.remote.interceptor

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import com.runyang.bridge.maintenance.util.NetworkException
import dagger.hilt.android.qualifiers.ApplicationContext
import okhttp3.Interceptor
import okhttp3.Response
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 网络拦截器
 * 检查网络连接状态，添加通用请求头
 */
@Singleton
class NetworkInterceptor @Inject constructor(
    @ApplicationContext private val context: Context
) : Interceptor {

    companion object {
        private const val HEADER_USER_AGENT = "User-Agent"
        private const val HEADER_ACCEPT = "Accept"
        private const val HEADER_CONTENT_TYPE = "Content-Type"
        private const val HEADER_ACCEPT_LANGUAGE = "Accept-Language"
        
        private const val USER_AGENT_VALUE = "RunYangBridge-Android/1.0.0"
        private const val ACCEPT_VALUE = "application/json"
        private const val CONTENT_TYPE_VALUE = "application/json; charset=utf-8"
        private const val ACCEPT_LANGUAGE_VALUE = "zh-CN,zh;q=0.9,en;q=0.8"
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        // 检查网络连接
        if (!isNetworkAvailable()) {
            throw NetworkException.NoConnectivityException("没有可用的网络连接")
        }

        // 添加通用请求头
        val originalRequest = chain.request()
        val requestWithHeaders = originalRequest.newBuilder()
            .header(HEADER_USER_AGENT, USER_AGENT_VALUE)
            .header(HEADER_ACCEPT, ACCEPT_VALUE)
            .header(HEADER_ACCEPT_LANGUAGE, ACCEPT_LANGUAGE_VALUE)
            .apply {
                // 只为POST, PUT, PATCH请求添加Content-Type
                if (originalRequest.method in setOf("POST", "PUT", "PATCH")) {
                    header(HEADER_CONTENT_TYPE, CONTENT_TYPE_VALUE)
                }
            }
            .build()

        return try {
            val response = chain.proceed(requestWithHeaders)
            
            // 检查响应状态码
            when (response.code) {
                in 200..299 -> response
                400 -> throw NetworkException.BadRequestException("请求参数错误")
                401 -> throw NetworkException.UnauthorizedException("未授权，请重新登录")
                403 -> throw NetworkException.ForbiddenException("没有权限访问此资源")
                404 -> throw NetworkException.NotFoundException("请求的资源不存在")
                408 -> throw NetworkException.TimeoutException("请求超时")
                in 500..599 -> throw NetworkException.ServerException("服务器内部错误")
                else -> throw NetworkException.UnknownException("未知错误: ${response.code}")
            }
        } catch (e: IOException) {
            when {
                e.message?.contains("timeout", ignoreCase = true) == true -> 
                    throw NetworkException.TimeoutException("连接超时")
                e.message?.contains("connection", ignoreCase = true) == true -> 
                    throw NetworkException.ConnectionException("连接失败")
                else -> throw NetworkException.UnknownException("网络请求失败: ${e.message}")
            }
        }
    }

    /**
     * 检查网络是否可用
     */
    private fun isNetworkAvailable(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        
        return if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
            val network = connectivityManager.activeNetwork
            val capabilities = connectivityManager.getNetworkCapabilities(network)
            
            capabilities?.let {
                it.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
                it.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED) &&
                (it.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) ||
                 it.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) ||
                 it.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET))
            } ?: false
        } else {
            @Suppress("DEPRECATION")
            val networkInfo = connectivityManager.activeNetworkInfo
            networkInfo?.isConnected == true
        }
    }

    /**
     * 获取网络类型
     */
    fun getNetworkType(): String {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        
        return if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
            val network = connectivityManager.activeNetwork
            val capabilities = connectivityManager.getNetworkCapabilities(network)
            
            when {
                capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> "WIFI"
                capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true -> "CELLULAR"
                capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) == true -> "ETHERNET"
                else -> "UNKNOWN"
            }
        } else {
            @Suppress("DEPRECATION")
            val networkInfo = connectivityManager.activeNetworkInfo
            when (networkInfo?.type) {
                ConnectivityManager.TYPE_WIFI -> "WIFI"
                ConnectivityManager.TYPE_MOBILE -> "CELLULAR"
                ConnectivityManager.TYPE_ETHERNET -> "ETHERNET"
                else -> "UNKNOWN"
            }
        }
    }

    /**
     * 检查是否为计费网络
     */
    fun isMeteredNetwork(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        return connectivityManager.isActiveNetworkMetered
    }
}