package com.runyang.bridge.maintenance.ui.auth

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.runyang.bridge.maintenance.data.local.datastore.TokenDataStore
import com.runyang.bridge.maintenance.data.remote.api.ApiService
import com.runyang.bridge.maintenance.data.remote.dto.AuthResponseDto
import com.runyang.bridge.maintenance.data.remote.dto.DeviceInfoDto
import com.runyang.bridge.maintenance.data.remote.dto.LoginRequestDto
import com.runyang.bridge.maintenance.util.NetworkException
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import retrofit2.Response
import java.util.UUID
import javax.inject.Inject

/**
 * 认证ViewModel
 * 处理登录、登出和认证状态管理
 */
@HiltViewModel
class AuthViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val apiService: ApiService,
    private val tokenDataStore: TokenDataStore
) : ViewModel() {

    private val _authState = MutableStateFlow(AuthState())
    val authState: StateFlow<AuthState> = _authState.asStateFlow()

    private val _loginState = MutableStateFlow(LoginState())
    val loginState: StateFlow<LoginState> = _loginState.asStateFlow()

    init {
        // 检查是否已登录
        checkLoginStatus()
    }

    /**
     * 检查登录状态
     */
    private fun checkLoginStatus() {
        viewModelScope.launch {
            try {
                val accessToken = tokenDataStore.accessToken.first()
                val userId = tokenDataStore.userId.first()
                val username = tokenDataStore.username.first()

                if (!accessToken.isNullOrBlank() && !userId.isNullOrBlank()) {
                    _authState.value = _authState.value.copy(
                        isLoggedIn = true,
                        userId = userId,
                        username = username ?: ""
                    )
                }
            } catch (e: Exception) {
                // 检查登录状态失败，保持未登录状态
                _authState.value = _authState.value.copy(isLoggedIn = false)
            }
        }
    }

    /**
     * 用户登录
     */
    fun login(
        serverUrl: String,
        username: String,
        password: String,
        rememberMe: Boolean = true
    ) {
        viewModelScope.launch {
            _loginState.value = _loginState.value.copy(
                isLoading = true,
                error = null
            )

            try {
                // 生成设备信息
                val deviceInfo = DeviceInfoDto(
                    brand = android.os.Build.BRAND,
                    model = android.os.Build.MODEL,
                    androidVersion = android.os.Build.VERSION.RELEASE,
                    appVersion = "1.0.0"
                )

                // 获取或生成设备ID
                val deviceId = tokenDataStore.deviceId.first() ?: generateDeviceId()

                val loginRequest = LoginRequestDto(
                    username = username,
                    password = password,
                    deviceId = deviceId,
                    platform = "android",
                    deviceInfo = deviceInfo
                )

                // 调用登录API
                val response: Response<AuthResponseDto> = apiService.login(loginRequest)

                if (response.isSuccessful && response.body() != null) {
                    val authResponse = response.body()!!

                    if (authResponse.success && !authResponse.accessToken.isNullOrBlank()) {
                        // 保存令牌和用户信息
                        tokenDataStore.saveTokens(
                            accessToken = authResponse.accessToken!!,
                            refreshToken = authResponse.refreshToken ?: "",
                            tokenType = authResponse.tokenType,
                            expiresIn = authResponse.expiresIn,
                            userId = authResponse.user?.id.toString(),
                            username = authResponse.user?.username
                        )

                        // 保存设备ID
                        if (deviceId.isNotBlank()) {
                            tokenDataStore.saveDeviceId(deviceId)
                        }

                        // 更新认证状态
                        _authState.value = _authState.value.copy(
                            isLoggedIn = true,
                            userId = authResponse.user?.id.toString() ?: "",
                            username = authResponse.user?.username ?: username,
                            userRole = authResponse.user?.role ?: "user",
                            fullName = authResponse.user?.fullName,
                            email = authResponse.user?.email,
                            department = authResponse.user?.department
                        )

                        _loginState.value = _loginState.value.copy(
                            isLoading = false,
                            isSuccess = true,
                            error = null
                        )
                    } else {
                        _loginState.value = _loginState.value.copy(
                            isLoading = false,
                            error = authResponse.message.ifBlank { "登录失败" }
                        )
                    }
                } else {
                    val errorMessage = when (response.code()) {
                        401 -> "用户名或密码错误"
                        404 -> "服务器地址无效"
                        500 -> "服务器内部错误"
                        else -> "网络连接失败，请检查网络设置"
                    }

                    _loginState.value = _loginState.value.copy(
                        isLoading = false,
                        error = errorMessage
                    )
                }
            } catch (e: Exception) {
                val errorMessage = when (e) {
                    is NetworkException -> e.message ?: "网络连接失败"
                    else -> "登录过程中发生未知错误"
                }

                _loginState.value = _loginState.value.copy(
                    isLoading = false,
                    error = errorMessage
                )
            }
        }
    }

    /**
     * 用户登出
     */
    fun logout() {
        viewModelScope.launch {
            try {
                // 清除本地存储的令牌
                tokenDataStore.clearTokens()

                // 重置状态
                _authState.value = AuthState()
                _loginState.value = LoginState()
            } catch (e: Exception) {
                // 登出失败时仍然重置本地状态
                _authState.value = AuthState()
                _loginState.value = LoginState()
            }
        }
    }

    /**
     * 清除登录状态（用于重置表单）
     */
    fun clearLoginState() {
        _loginState.value = LoginState()
    }

    /**
     * 生成设备ID
     */
    private fun generateDeviceId(): String {
        return "android_${UUID.randomUUID().toString().replace("-", "")}"
    }
}

/**
 * 认证状态数据类
 */
data class AuthState(
    val isLoggedIn: Boolean = false,
    val userId: String = "",
    val username: String = "",
    val userRole: String = "user",
    val fullName: String? = null,
    val email: String? = null,
    val department: String? = null
)

/**
 * 登录状态数据类
 */
data class LoginState(
    val isLoading: Boolean = false,
    val isSuccess: Boolean = false,
    val error: String? = null
)