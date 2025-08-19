// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    id("com.android.application") version "8.1.4" apply false
    id("com.android.library") version "8.1.4" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
    id("com.google.dagger.hilt.android") version "2.49" apply false
    id("org.jetbrains.kotlin.plugin.serialization") version "1.9.22" apply false
}

// 定义项目范围的配置
ext {
    set("compileSdkVersion", 34)
    set("minSdkVersion", 24)
    set("targetSdkVersion", 34)
    set("versionCode", 1)
    set("versionName", "1.0.0")
    
    // 依赖版本管理
    set("kotlinVersion", "1.9.22")
    set("composeVersion", "2024.02.00")
    set("hiltVersion", "2.49")
    set("retrofitVersion", "2.9.0")
    set("roomVersion", "2.6.1")
    set("coroutinesVersion", "1.7.3")
    set("lifecycleVersion", "2.7.0")
    set("navigationVersion", "2.7.6")
    set("workVersion", "2.9.0")
    set("accompanistVersion", "0.32.0")
}

tasks.register("clean", Delete::class) {
    delete(rootProject.buildDir)
}