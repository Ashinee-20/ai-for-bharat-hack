# FarmIntel Android App - Offline LLM Support

## Setup

### Prerequisites
- Android Studio 4.2+
- Android SDK 21+
- MLC-LLM runtime
- TinyLlama 1.1B Q4 model (~550MB)

### Installation

1. **Clone and setup:**
```bash
cd farmintel-v1/mobile/android
./gradlew build
```

2. **Download TinyLlama model:**
```bash
# Download from Hugging Face
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Place in app assets
mv tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf app/src/main/assets/models/
```

3. **Build and run:**
```bash
./gradlew installDebug
```

## Architecture

**Online Mode:**
- Connects to AWS Lambda (Groq LLM)
- Real-time prices & insights
- Full agricultural AI capabilities

**Offline Mode:**
- TinyLlama 1.1B Q4 runs locally
- MLC-LLM runtime handles inference
- 2-4 tokens/sec on mid-range phones
- 4-8 second response time

## Model Details

- **Model:** TinyLlama 1.1B Chat v1.0
- **Quantization:** Q4_K_M (4-bit)
- **Size:** ~550MB
- **Runtime:** MLC-LLM
- **Inference Speed:** 2-4 tokens/sec
- **Memory:** ~1.5GB during inference

## File Structure

```
android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── assets/
│   │   │   │   └── models/
│   │   │   │       └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
│   │   │   ├── java/
│   │   │   │   └── com/farmintel/
│   │   │   │       ├── MainActivity.kt
│   │   │   │       ├── OfflineLLMManager.kt
│   │   │   │       ├── HybridModeHandler.kt
│   │   │   │       └── CacheManager.kt
│   │   │   └── res/
│   │   │       ├── layout/
│   │   │       └── values/
│   ├── build.gradle
│   └── proguard-rules.pro
├── build.gradle
├── settings.gradle
└── gradle.properties
```

## Key Components

### OfflineLLMManager.kt
Manages TinyLlama inference using MLC-LLM runtime.

### HybridModeHandler.kt
Switches between online (Groq) and offline (TinyLlama) modes.

### CacheManager.kt
SQLite database for caching prices and insights.

## Usage

```kotlin
// Initialize
val llmManager = OfflineLLMManager(context)
val hybridHandler = HybridModeHandler(llmManager)

// Process query
val result = hybridHandler.processQuery("What is the price of wheat?")

// Result contains:
// - response: String (LLM response)
// - mode: "online" | "offline"
// - cached: Boolean
```

## Performance

**First Run:**
- Model loading: ~2-3 seconds
- Inference: 4-8 seconds
- Total: 6-11 seconds

**Subsequent Runs:**
- Model cached in memory
- Inference: 4-8 seconds

**Network Latency:**
- Online: 1.5-2 seconds (AWS Lambda)
- Offline: 0 seconds (local)

## Dependencies

```gradle
dependencies {
    // MLC-LLM
    implementation 'org.mlc-ai:mlc-llm:0.1.0'
    
    // Networking
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    
    // Database
    implementation 'androidx.room:room-runtime:2.5.1'
    
    // Coroutines
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.1'
}
```

## Troubleshooting

**Model not loading:**
- Check model file exists in assets/models/
- Verify file permissions
- Check available storage (need ~2GB)

**Slow inference:**
- Close background apps
- Check device temperature
- Reduce batch size

**Memory issues:**
- Reduce model size (use Q3 instead of Q4)
- Clear cache periodically
- Monitor memory usage

## Next Steps

1. Fine-tune TinyLlama on agricultural data (QLoRA)
2. Add image recognition for pest/disease detection
3. Implement voice input/output
4. Add multi-language support
5. Create offline map for mandi locations
