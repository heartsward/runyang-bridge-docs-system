package com.runyang.bridge.maintenance.util

/**
 * 网络异常类
 * 定义各种网络请求相关的异常
 */
sealed class NetworkException(
    override val message: String,
    override val cause: Throwable? = null
) : Exception(message, cause) {

    /**
     * 无网络连接异常
     */
    class NoConnectivityException(message: String) : NetworkException(message)

    /**
     * 连接异常
     */
    class ConnectionException(message: String) : NetworkException(message)

    /**
     * 超时异常
     */
    class TimeoutException(message: String) : NetworkException(message)

    /**
     * 请求参数错误 (400)
     */
    class BadRequestException(message: String) : NetworkException(message)

    /**
     * 未授权异常 (401)
     */
    class UnauthorizedException(message: String) : NetworkException(message)

    /**
     * 禁止访问异常 (403)
     */
    class ForbiddenException(message: String) : NetworkException(message)

    /**
     * 资源未找到异常 (404)
     */
    class NotFoundException(message: String) : NetworkException(message)

    /**
     * 服务器内部错误 (5xx)
     */
    class ServerException(message: String) : NetworkException(message)

    /**
     * 未知异常
     */
    class UnknownException(message: String, cause: Throwable? = null) : NetworkException(message, cause)

    /**
     * 解析异常
     */
    class ParseException(message: String, cause: Throwable? = null) : NetworkException(message, cause)

    /**
     * 获取用户友好的错误消息
     */
    fun getUserFriendlyMessage(): String {
        return when (this) {
            is NoConnectivityException -> "网络连接不可用，请检查网络设置"
            is ConnectionException -> "连接服务器失败，请稍后重试"
            is TimeoutException -> "请求超时，请检查网络连接后重试"
            is BadRequestException -> "请求参数有误，请检查输入内容"
            is UnauthorizedException -> "登录已过期，请重新登录"
            is ForbiddenException -> "没有权限执行此操作"
            is NotFoundException -> "请求的内容不存在"
            is ServerException -> "服务器暂时不可用，请稍后重试"
            is ParseException -> "数据解析失败，请稍后重试"
            is UnknownException -> "未知错误，请稍后重试"
        }
    }

    /**
     * 获取错误代码
     */
    fun getErrorCode(): String {
        return when (this) {
            is NoConnectivityException -> "NO_CONNECTIVITY"
            is ConnectionException -> "CONNECTION_ERROR"
            is TimeoutException -> "TIMEOUT"
            is BadRequestException -> "BAD_REQUEST"
            is UnauthorizedException -> "UNAUTHORIZED"
            is ForbiddenException -> "FORBIDDEN"
            is NotFoundException -> "NOT_FOUND"
            is ServerException -> "SERVER_ERROR"
            is ParseException -> "PARSE_ERROR"
            is UnknownException -> "UNKNOWN_ERROR"
        }
    }

    /**
     * 是否为可重试的错误
     */
    fun isRetryable(): Boolean {
        return when (this) {
            is NoConnectivityException,
            is ConnectionException,
            is TimeoutException,
            is ServerException -> true
            else -> false
        }
    }
}