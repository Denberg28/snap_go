plugins { id("com.android.application") }

android {
    namespace = "com.snapgo.operator"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.snapgo.operator"
        minSdk = 26
        targetSdk = 35
        versionCode = 4
        versionName = "0.4.0"
    }
    signingConfigs {
        create("snapGoRelease") {
            val keyFile = System.getenv("SNAP_GO_KEYSTORE_FILE")
            if (keyFile != null) storeFile = file(keyFile)
            storePassword = System.getenv("SNAP_GO_SIGNING_PASSWORD")
            keyAlias = "snapgo"
            keyPassword = System.getenv("SNAP_GO_SIGNING_PASSWORD")
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
