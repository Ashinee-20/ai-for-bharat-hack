"""
Local LLM Integration - TinyLlama Model
Enables offline LLM inference using GGUF model
"""

import os
from pathlib import Path
from typing import Optional, List, Dict

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


class LocalLLMManager:
    """Manage local LLM inference with TinyLlama"""
    
    def __init__(self, model_path: str = None):
        """
        Initialize local LLM manager
        
        Args:
            model_path: Path to GGUF model file
        """
        self.model_path = model_path or self._find_model()
        self.model = None
        self.is_loaded = False
        
        if self.model_path and os.path.exists(self.model_path):
            self._load_model()
        else:
            print(f"[WARNING] Model not found at {self.model_path}")
    
    def _find_model(self) -> Optional[str]:
        """Find TinyLlama model in common locations"""
        possible_paths = [
            "tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
            "../tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
            "../../tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
            os.path.expanduser("~/tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[INFO] Found model at: {path}")
                return path
        
        return None
    
    def _load_model(self):
        """Load the GGUF model"""
        if not Llama:
            print("[ERROR] llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            return
        
        try:
            print(f"[INFO] Loading model from {self.model_path}...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=512,  # Context window
                n_threads=4,  # CPU threads
                n_gpu_layers=0,  # CPU only (set to -1 for GPU if available)
                verbose=False
            )
            self.is_loaded = True
            print("[INFO] Model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            self.is_loaded = False
    
    def generate(self, prompt: str, max_tokens: int = 150, temperature: float = 0.3) -> str:
        """
        Generate response using local LLM
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.is_loaded or not self.model:
            return ""
        
        try:
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
                stop=["User:", "Assistant:"]
            )
            return response["choices"][0]["text"].strip()
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return ""
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 150) -> str:
        """
        Chat-style generation
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        if not self.is_loaded or not self.model:
            return ""
        
        # Format messages for TinyLlama
        prompt = self._format_chat_prompt(messages)
        return self.generate(prompt, max_tokens)
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into prompt for TinyLlama"""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            prompt += f"{role}: {content}\n"
        prompt += "Assistant: "
        return prompt
    
    def is_available(self) -> bool:
        """Check if local LLM is available"""
        return self.is_loaded and self.model is not None


# Global instance
_local_llm = None


def get_local_llm(model_path: str = None) -> LocalLLMManager:
    """Get or create local LLM instance"""
    global _local_llm
    if _local_llm is None:
        _local_llm = LocalLLMManager(model_path)
    return _local_llm
