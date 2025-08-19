pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // 如果需要JitPack等其他仓库可以在这里添加
        // maven { url = uri("https://jitpack.io") }
    }
}

rootProject.name = "RunYang Bridge Maintenance"
include(":app")
