plugins { id("com.android.application") }

android {
    namespace = "com.snapgo.operator"
    buildFeatures { buildConfig = true }
    compileSdk = 35
    defaultConfig {
        applicationId = "com.snapgo.operator"
        minSdk = 26
        targetSdk = 35
        versionCode = 15
        versionName = "0.11.4"
    }
    signingConfigs {
        create("snapGoRelease") {
            val keyFile = System.getenv("SNAP_GO_KEYSTORE_FILE")
            if (keyFile != null) storeFile = file(keyFile)
            storePassword = System.getenv("SNAP_GO_SIGNING_PASSWORD")
            keyAlias = System.getenv("SNAP_GO_KEY_ALIAS") ?: "snapgo"
            keyPassword = System.getenv("SNAP_GO_KEY_PASSWORD") ?: System.getenv("SNAP_GO_SIGNING_PASSWORD")
        }
    }
    buildTypes {
        getByName("release") {
            signingConfig = signingConfigs.getByName("snapGoRelease")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
