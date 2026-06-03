import java.io.FileInputStream
import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

val localProperties = Properties().apply {
    val localPropertiesFile = rootProject.file("local.properties")
    if (localPropertiesFile.exists()) {
        FileInputStream(localPropertiesFile).use { load(it) }
    }
}

val keystoreProperties = Properties().apply {
    val keystorePropertiesFile = rootProject.file("keystore.properties")
    if (keystorePropertiesFile.exists()) {
        FileInputStream(keystorePropertiesFile).use { load(it) }
    }
}

val hasReleaseKeystore = listOf("storeFile", "storePassword", "keyAlias", "keyPassword")
    .all { !keystoreProperties.getProperty(it).isNullOrBlank() }

val allowDirectProviderKeys = (
    localProperties.getProperty("SIGURSCAN_ENABLE_DIRECT_PROVIDER_KEYS")
        ?: localProperties.getProperty("NUDACLICK_ENABLE_DIRECT_PROVIDER_KEYS")
        ?: System.getenv("SIGURSCAN_ENABLE_DIRECT_PROVIDER_KEYS")
        ?: System.getenv("NUDACLICK_ENABLE_DIRECT_PROVIDER_KEYS")
        ?: "false"
    ).trim().lowercase() in setOf("1", "true", "yes", "on")

fun buildConfigSafeString(key: String, envFallback: String): String {
    val value = (localProperties.getProperty(key) ?: System.getenv(envFallback) ?: "").trim()
    return "\"${value.replace("\\", "\\\\").replace("\"", "\\\"")}\""
}

fun buildConfigSafeString(primaryKey: String, legacyKey: String, primaryEnv: String, legacyEnv: String): String {
    val value = (
        localProperties.getProperty(primaryKey)
            ?: localProperties.getProperty(legacyKey)
            ?: System.getenv(primaryEnv)
            ?: System.getenv(legacyEnv)
            ?: ""
        ).trim()
    return "\"${value.replace("\\", "\\\\").replace("\"", "\\\"")}\""
}

fun providerBuildConfigSafeString(key: String, envFallback: String): String {
    return if (allowDirectProviderKeys) {
        buildConfigSafeString(key, envFallback)
    } else {
        "\"\""
    }
}

fun providerBuildConfigSafeString(primaryKey: String, legacyKey: String, primaryEnv: String, legacyEnv: String): String {
    return if (allowDirectProviderKeys) {
        buildConfigSafeString(primaryKey, legacyKey, primaryEnv, legacyEnv)
    } else {
        "\"\""
    }
}

android {
    namespace = "ro.sigurscan.app"
    compileSdk {
        version = release(36) {
            minorApiLevel = 1
        }
    }

    defaultConfig {
        applicationId = "ro.sigurscan.app"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        buildConfigField(
            "String",
            "SIGURSCAN_BACKEND_BASE_URL",
            buildConfigSafeString(
                primaryKey = "SIGURSCAN_BACKEND_BASE_URL",
                legacyKey = "NUDACLICK_BACKEND_BASE_URL",
                primaryEnv = "SIGURSCAN_BACKEND_BASE_URL",
                legacyEnv = "NUDACLICK_BACKEND_BASE_URL"
            )
        )
        buildConfigField(
            "String",
            "URLSCAN_API_KEY",
            providerBuildConfigSafeString(
                primaryKey = "SIGURSCAN_URLSCAN_API_KEY",
                legacyKey = "NUDACLICK_URLSCAN_API_KEY",
                primaryEnv = "SIGURSCAN_URLSCAN_API_KEY",
                legacyEnv = "NUDACLICK_URLSCAN_API_KEY"
            )
        )
        buildConfigField(
            "String",
            "VIRUS_TOTAL_API_KEY",
            providerBuildConfigSafeString(
                primaryKey = "SIGURSCAN_VIRUS_TOTAL_API_KEY",
                legacyKey = "NUDACLICK_VIRUS_TOTAL_API_KEY",
                primaryEnv = "SIGURSCAN_VIRUS_TOTAL_API_KEY",
                legacyEnv = "NUDACLICK_VIRUS_TOTAL_API_KEY"
            )
        )
        buildConfigField(
            "String",
            "GOOGLE_WEB_RISK_API_KEY",
            providerBuildConfigSafeString(
                primaryKey = "SIGURSCAN_GOOGLE_WEB_RISK_API_KEY",
                legacyKey = "NUDACLICK_GOOGLE_SAFE_BROWSING_API_KEY",
                primaryEnv = "SIGURSCAN_GOOGLE_WEB_RISK_API_KEY",
                legacyEnv = "NUDACLICK_GOOGLE_SAFE_BROWSING_API_KEY"
            )
        )
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        if (hasReleaseKeystore) {
            create("release") {
                storeFile = rootProject.file(keystoreProperties.getProperty("storeFile"))
                storePassword = keystoreProperties.getProperty("storePassword")
                keyAlias = keystoreProperties.getProperty("keyAlias")
                keyPassword = keystoreProperties.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            buildConfigField("String", "URLSCAN_API_KEY", "\"\"")
            buildConfigField("String", "VIRUS_TOTAL_API_KEY", "\"\"")
            buildConfigField("String", "GOOGLE_WEB_RISK_API_KEY", "\"\"")
            if (hasReleaseKeystore) {
                signingConfig = signingConfigs.getByName("release")
            }
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        isCoreLibraryDesugaringEnabled = true
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.compose.material.icons.extended)
    implementation("io.coil-kt:coil-compose:2.6.0")
    implementation(libs.gson)
    implementation(libs.google.mlkit.text.recognition)
    implementation(libs.google.mlkit.barcode)
    implementation(libs.retrofit)
    implementation(libs.retrofit.gson)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    
    implementation(libs.androidx.camera.core)
    implementation(libs.androidx.camera.lifecycle)
    implementation(libs.androidx.camera.camera2)
    implementation(libs.androidx.camera.view)

    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")

    testImplementation(libs.junit)
    testImplementation("org.apache.pdfbox:pdfbox:2.0.31")
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
}
