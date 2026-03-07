# FarmIntel Desktop App - Offline LLM Support

## Setup

### Prerequisites
- Python 3.9+
- llama.cpp (compiled)
- TinyLlama 1.1B Q4 model (~550MB)
- PyQt5 or Tkinter for GUI

### Installation

1. **Clone llama.cpp:**
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make
```

2. **Download TinyLlama model:**
```bash
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
mv tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf ./models/
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run desktop app:**
```bash
python main.py
```

## Architecture

**Online Mode:**
- Connects to AWS Lambda (Groq LLM)
- Real-time prices & insights
- Full agricultural AI capabilities

**Offline Mode:**
- TinyLlama 1.1B Q4 runs locally via llama.cpp
- 4-8 tokens/sec on modern CPUs
- 2-4 second response time

## Model Details

- **Model:** TinyLlama 1.1B Chat v1.0
- **Quantization:** Q4_K_M (4-bit)
- **Size:** ~550MB
- **Runtime:** llama.cpp
- **Inference Speed:** 4-8 tokens/sec
- **Memory:** ~1.5GB during inference

## File Structure

```
desktop/
├── main.py                    # Main application
├── offline_llm_manager.py     # TinyLlama inference
├── hybrid_mode_handler.py     # Online/offline switching
├── cache_manager.py           # SQLite caching
├── ui/
│   ├── main_window.py         # Main UI
│   ├── chat_widget.py         # Chat interface
│   └── status_indicator.py    # Status display
├── models/
│   └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
├── requirements.txt
└── config.yaml
```

## Key Components

### offline_llm_manager.py
Manages TinyLlama inference using llama.cpp subprocess.

### hybrid_mode_handler.py
Switches between online (Groq) and offline (TinyLlama) modes.

### cache_manager.py
SQLite database for caching prices and insights.

### ui/main_window.py
PyQt5 GUI for chat interface.

## Usage

```python
from offline_llm_manager import OfflineLLMManager
from hybrid_mode_handler import HybridModeHandler

# Initialize
llm_manager = OfflineLLMManager(model_path='./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')
hybrid_handler = HybridModeHandler(llm_manager)

# Process query
result = hybrid_handler.process_query("What is the price of wheat?")

# Result contains:
# - response: str (LLM response)
# - mode: "online" | "offline"
# - cached: bool
```

## Performance

**First Run:**
- Model loading: ~1-2 seconds
- Inference: 2-4 seconds
- Total: 3-6 seconds

**Subsequent Runs:**
- Model cached in memory
- Inference: 2-4 seconds

**Network Latency:**
- Online: 1.5-2 seconds (AWS Lambda)
- Offline: 0 seconds (local)

## Dependencies

```
requests==2.31.0
PyQt5==5.15.9
sqlite3 (built-in)
pyyaml==6.0
```

## Configuration

Edit `config.yaml`:

```yaml
online:
  api_url: "https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod"
  timeout: 5

offline:
  model_path: "./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
  llama_cpp_path: "./llama.cpp/main"
  threads: 4
  context_size: 512

cache:
  db_path: "./cache/farmintel.db"
  ttl_hours: 24
```

## Running

### GUI Mode (Recommended)
```bash
python main.py --gui
```

### CLI Mode
```bash
python main.py --cli
```

### Headless Mode
```bash
python main.py --headless
```

## Troubleshooting

**Model not found:**
- Check model path in config.yaml
- Verify file exists and is readable
- Check disk space (need ~2GB)

**Slow inference:**
- Increase threads in config.yaml
- Close other applications
- Check CPU temperature

**Memory issues:**
- Reduce context_size in config.yaml
- Use Q3 quantization instead of Q4
- Monitor memory with `top` or Task Manager

## Performance Optimization

**For faster inference:**
```yaml
offline:
  threads: 8  # Increase based on CPU cores
  context_size: 256  # Reduce context
```

**For better quality:**
```yaml
offline:
  threads: 4
  context_size: 512
```

## Next Steps

1. Fine-tune TinyLlama on agricultural data (QLoRA)
2. Add image recognition for pest/disease detection
3. Implement voice input/output
4. Add multi-language support
5. Create offline map for mandi locations
6. Package as standalone executable (PyInstaller)

## Building Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

This creates a single executable that includes Python, all dependencies, and the GUI.
