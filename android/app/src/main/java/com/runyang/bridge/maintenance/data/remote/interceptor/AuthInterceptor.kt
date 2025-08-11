package com.runyang.bridge.maintenance.data.remote.interceptor

import com.runyang.bridge.maintenance.data.local.datastore.TokenDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 认证拦截器
 * 自动在请求头中添加Authorization令牌
 */
@Singleton
class AuthInterceptor @Inject constructor(
    private val tokenDataStore: TokenDataStore
) : Interceptor {

    companion object {
        private const val AUTHORIZATION_HEADER = "Authorization"
        private const val BEARER_PREFIX = "Bearer "
        
        // 不需要认证的端点
        private val NO_AUTH_ENDPOINTS = setOf(
            "/system/health",
            "/system/version",
            "/system/capabilities",
            "/system/info",
            "/mobile/auth/login"
        )
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val url = originalRequest.url.toString()

        // 检查是否需要认证
        val needsAuth = !NO_AUTH_ENDPOINTS.any { endpoint ->
            url.contains(endpoint)
        }

        return if (needsAuth) {
            // 获取访问令牌
            val accessToken = runBlocking {
                try {
                    tokenDataStore.accessToken.first()
                } catch (e: Exception) {
                    null
                }
            }

            if (accessToken != null) {
                // 添加认证头
                val authenticatedRequest = originalRequest.newBuilder()
                    .header(AUTHORIZATION_HEADER, BEARER_PREFIX + accessToken)
                    .build()

                val response = chain.proceed(authenticatedRequest)

                // 如果返回401未授权，可能需要刷新令牌
                if (response.code == 401) {
                    response.close()
                    handleTokenRefresh(chain, originalRequest)
                } else {
                    response
                }
            } else {
                // 没有访问令牌，直接发送请求
                chain.proceed(originalRequest)
            }
        } else {
            // 不需要认证的请求
            chain.proceed(originalRequest)
        }
    }

    /**
     * 处理令牌刷新
     */
    private fun handleTokenRefresh(chain: Interceptor.Chain, originalRequest: okhttp3.Request): Response {
        return runBlocking {
            try {
                val refreshToken = tokenDataStore.refreshToken.first()
                
                if (refreshToken != null) {
                    // 这里应该调用刷新令牌的API
                    // 为了避免循环依赖，暂时返回原始请求结果
                    // 实际实现中，可以通过事件总线或其他方式通知需要刷新令牌
                    
                    // 暂时直接继续原始请求
                    chain.proceed(originalRequest)
                } else {
                    // 没有刷新令牌，返回原始请求结果
                    chain.proceed(originalRequest)
                }
            } catch (e: Exception) {
                // 刷新失败，返回原始请求结果
                chain.proceed(originalRequest)
            }
        }
    }
}