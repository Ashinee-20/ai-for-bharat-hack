# FarmIntel Offline Module

Offline LLM inference using TinyLlama 1.1B model with skill-based response generation.

## 📁 Directory Structure

```
offline/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── local_llm.py                # Local LLM manager (TinyLlama)
├── offline_router.py           # Query routing & response generation
├── cache_manager.py            # SQLite cache management
├── hybrid_mode.py              # Online/offline switching
├── offline_integration.js      # Frontend integration
├── example_usage.py            # Usage examples
├── test_simple.py              # Simple test script
└── offline_cache/              # Cache directory (auto-created)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python test_simple.py
```

### 3. Use in Your Code
```python
from offline.hybrid_mode import HybridModeHandler

handler = HybridModeHandler("https://your-api.com")
result = handler.process_query("What is the price of wheat?")
print(result['response'])
```

## 📚 Core Files

### `local_llm.py`
Local LLM manager using llama-cpp-python
- Model loading and inference
- Chat and generation modes
- Automatic model detection

### `offline_router.py`
Query routing and response generation
- Skill detection (8 domains)
- Query classification
- Response generation with skill context

### `cache_manager.py`
SQLite-based cache management
- Price and insight caching
- TTL-based expiration
- Cache statistics

### `hybrid_mode.py`
Online/offline switching
- Automatic fallback mechanism
- Response caching
- Status indicators

## 🧪 Testing

### Simple Test
```bash
python test_simple.py
```

Shows:
- LLM availability
- Skill detection
- Query routing
- Response generation

### Usage Examples
```bash
python example_usage.py
```

Shows 6 practical examples of using the offline system.

## 🎯 Supported Query Types

1. **Price** - Mandi prices, market trends
2. **Weather** - Temperature, rainfall, drought
3. **Soil** - pH, nutrients, fertility
4. **Pest** - Identification, organic control
5. **Disease** - Symptoms, prevention, treatment
6. **Irrigation** - Water requirements, scheduling
7. **Fertilizer** - NPK ratios, application timing
8. **Harvest** - Maturity indicators, storage

## 🌐 Languages

- English: Full support
- Hindi: Keywords and responses in Devanagari

## ⚙️ Configuration

### Model Parameters (in `local_llm.py`)
```python
n_ctx=512           # Context window
n_threads=4         # CPU threads
n_gpu_layers=0      # GPU layers (0=CPU only)
max_tokens=150      # Response length
temperature=0.3     # Determinism
```

## 📊 Performance

- First query: 2-3 seconds (model loading)
- Subsequent queries: 1-2 seconds
- Model size: 400MB
- Memory usage: 600-700MB

## 🔗 Integration

### Backend (Python)
```python
from offline.hybrid_mode import HybridModeHandler

handler = HybridModeHandler("https://your-api.com")
result = handler.process_query("Your question here")
```

### Frontend (JavaScript)
```javascript
const offlineManager = new OfflineManager();
const result = await offlineManager.processQuery("Your question");
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Model not found | Copy model to `farmintel-v1/` directory |
| llama-cpp-python error | `pip install llama-cpp-python` |
| Slow inference | Increase `n_threads`, enable GPU |
| Out of memory | Reduce `n_ctx`, reduce `n_threads` |

## 📖 Documentation

- **Setup Guide**: `../OFFLINE_LLM_SETUP.md`
- **Integration Guide**: `../OFFLINE_INTEGRATION_GUIDE.md`
- **Quick Reference**: `../QUICK_OFFLINE_REFERENCE.md`
- **Testing Guide**: `../TEST_OFFLINE_MODEL.md`

## ✅ Features

✓ Local LLM inference (TinyLlama 1.1B)
✓ Hybrid online/offline mode
✓ Automatic fallback mechanism
✓ Query routing (8 types)
✓ Response generation with skills
✓ Cache integration
✓ Multilingual support
✓ Performance optimized

## 📞 Support

For issues or questions, check the documentation files or run the test script to diagnose problems.

---

**Status**: Production Ready ✅
