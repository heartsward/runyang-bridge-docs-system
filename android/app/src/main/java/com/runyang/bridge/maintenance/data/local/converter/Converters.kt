package com.runyang.bridge.maintenance.data.local.converter

import androidx.room.TypeConverter
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

/**
 * Room数据库类型转换器
 * 用于将复杂数据类型转换为数据库可存储的类型
 */
class Converters {

    companion object {
        private val gson = Gson()
    }

    /**
     * 字符串列表转换
     */
    @TypeConverter
    fun fromStringList(value: List<String>?): String? {
        return if (value == null) null else gson.toJson(value)
    }

    @TypeConverter
    fun toStringList(value: String?): List<String> {
        return if (value == null) {
            emptyList()
        } else {
            try {
                val listType = object : TypeToken<List<String>>() {}.type
                gson.fromJson(value, listType) ?: emptyList()
            } catch (e: Exception) {
                emptyList()
            }
        }
    }

    /**
     * Map<String, Any>转换
     */
    @TypeConverter
    fun fromStringAnyMap(value: Map<String, Any>?): String? {
        return if (value == null || value.isEmpty()) null else gson.toJson(value)
    }

    @TypeConverter
    fun toStringAnyMap(value: String?): Map<String, Any> {
        return if (value == null) {
            emptyMap()
        } else {
            try {
                val mapType = object : TypeToken<Map<String, Any>>() {}.type
                gson.fromJson(value, mapType) ?: emptyMap()
            } catch (e: Exception) {
                emptyMap()
            }
        }
    }

    /**
     * Map<String, String>转换
     */
    @TypeConverter
    fun fromStringStringMap(value: Map<String, String>?): String? {
        return if (value == null || value.isEmpty()) null else gson.toJson(value)
    }

    @TypeConverter
    fun toStringStringMap(value: String?): Map<String, String> {
        return if (value == null) {
            emptyMap()
        } else {
            try {
                val mapType = object : TypeToken<Map<String, String>>() {}.type
                gson.fromJson(value, mapType) ?: emptyMap()
            } catch (e: Exception) {
                emptyMap()
            }
        }
    }

    /**
     * List<Int>转换
     */
    @TypeConverter
    fun fromIntList(value: List<Int>?): String? {
        return if (value == null) null else gson.toJson(value)
    }

    @TypeConverter
    fun toIntList(value: String?): List<Int> {
        return if (value == null) {
            emptyList()
        } else {
            try {
                val listType = object : TypeToken<List<Int>>() {}.type
                gson.fromJson(value, listType) ?: emptyList()
            } catch (e: Exception) {
                emptyList()
            }
        }
    }

    /**
     * Boolean转换（Room原生支持，这里为了一致性）
     */
    @TypeConverter
    fun fromBoolean(value: Boolean): Int {
        return if (value) 1 else 0
    }

    @TypeConverter
    fun toBoolean(value: Int): Boolean {
        return value != 0
    }
}