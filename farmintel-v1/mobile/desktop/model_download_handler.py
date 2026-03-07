"""
FarmIntel Desktop - Model Download Handler
Manages downloading and setting up the TinyLlama model on first run
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Callable, Optional
import threading
import time

class ModelDownloadHandler:
    """Handles model download with progress tracking"""
    
    def __init__(self, app_dir: str = None):
        self.app_dir = app_dir or os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(self.app_dir, 'models')
        self.config_file = os.path.join(self.app_dir, 'model_config.json')
        
        self.MODEL_NAME = 'tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf'
        self.MODEL_SIZE = 400 * 1024 * 1024  # 400MB
        self.MODEL_URL = 'https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf'
        
        self.progress_callback: Optional[Callable] = None
        self.download_thread: Optional[threading.Thread] = None
        
    def is_model_downloaded(self) -> bool:
        """Check if model is already downloaded"""
        model_path = os.path.join(self.models_dir, self.MODEL_NAME)
        
        if not os.path.exists(model_path):
            return False
            
        # Verify file size
        file_size = os.path.getsize(model_path)
        if file_size < self.MODEL_SIZE * 0.9:  # Allow 10% variance
            return False
            
        return True
    
    def get_model_path(self) -> str:
        """Get the path to the model file"""
        return os.path.join(self.models_dir, self.MODEL_NAME)
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """
        Set callback for download progress
        Callback receives (bytes_downloaded, total_bytes)
        """
        self.progress_callback = callback
    
    def download_model_async(self) -> threading.Thread:
        """Start model download in background thread"""
        self.download_thread = threading.Thread(target=self._download_model, daemon=False)
        self.download_thread.start()
        return self.download_thread
    
    def _download_model(self):
        """Download model from Hugging Face"""
        try:
            # Create models directory
            os.makedirs(self.models_dir, exist_ok=True)
            
            model_path = self.get_model_path()
            
            # Download with progress tracking
            response = requests.get(self.MODEL_URL, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if self.progress_callback:
                            self.progress_callback(downloaded, total_size)
            
            # Save config
            self._save_config({'model_downloaded': True, 'model_path': model_path})
            
            print(f"✓ Model downloaded successfully to {model_path}")
            
        except Exception as e:
            print(f"✗ Model download failed: {e}")
            # Clean up partial download
            if os.path.exists(model_path):
                try:
                    os.remove(model_path)
                except:
                    pass
            raise
    
    def _save_config(self, config: dict):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def _load_config(self) -> dict:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        return {}


class ModelDownloadUI:
    """Base class for model download UI (to be implemented by PyQt5/Tkinter)"""
    
    def __init__(self, handler: ModelDownloadHandler):
        self.handler = handler
        self.is_downloading = False
    
    def show_download_dialog(self) -> bool:
        """
        Show download dialog
        Returns True if user wants to download, False otherwise
        """
        raise NotImplementedError
    
    def update_progress(self, current: int, total: int):
        """Update progress display"""
        raise NotImplementedError
    
    def show_success(self):
        """Show success message"""
        raise NotImplementedError
    
    def show_error(self, error: str):
        """Show error message"""
        raise NotImplementedError


class PyQt5ModelDownloadUI(ModelDownloadUI):
    """PyQt5 implementation of model download UI"""
    
    def __init__(self, handler: ModelDownloadHandler, parent=None):
        super().__init__(handler)
        try:
            from PyQt5.QtWidgets import (
                QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                QProgressBar, QMessageBox
            )
            from PyQt5.QtCore import Qt, pyqtSignal, QThread
            
            self.QDialog = QDialog
            self.QVBoxLayout = QVBoxLayout
            self.QHBoxLayout = QHBoxLayout
            self.QLabel = QLabel
            self.QPushButton = QPushButton
            self.QProgressBar = QProgressBar
            self.QMessageBox = QMessageBox
            self.Qt = Qt
            self.pyqtSignal = pyqtSignal
            self.QThread = QThread
            
            self.parent = parent
            self.dialog = None
            self.progress_bar = None
            self.status_label = None
            
        except ImportError:
            raise ImportError("PyQt5 is required for GUI. Install with: pip install PyQt5")
    
    def show_download_dialog(self) -> bool:
        """Show download dialog and return user choice"""
        self.dialog = self.QDialog(self.parent)
        self.dialog.setWindowTitle("Download Offline Model")
        self.dialog.setGeometry(100, 100, 500, 300)
        
        layout = self.QVBoxLayout()
        
        # Title
        title = self.QLabel("📥 Download Offline Model")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = self.QLabel(
            "FarmIntel can work offline using a local AI model.\n"
            "Download it now for better performance and offline access.\n\n"
            "Model: TinyLlama 1.1B\n"
            "Size: ~400 MB\n"
            "Storage Required: 1 GB free space"
        )
        desc.setStyleSheet("color: #666; line-height: 1.6;")
        layout.addWidget(desc)
        
        # Benefits
        benefits = self.QLabel(
            "✨ Benefits:\n"
            "✓ Works completely offline\n"
            "✓ Faster response times\n"
            "✓ No internet required\n"
            "✓ Privacy - data stays local"
        )
        benefits.setStyleSheet("color: #333; margin: 10px 0;")
        layout.addWidget(benefits)
        
        # Progress bar (hidden initially)
        self.progress_bar = self.QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = self.QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = self.QHBoxLayout()
        
        skip_btn = self.QPushButton("Skip for Now")
        skip_btn.clicked.connect(lambda: self.dialog.reject())
        button_layout.addWidget(skip_btn)
        
        download_btn = self.QPushButton("Download Model")
        download_btn.setStyleSheet(
            "background-color: #10a37f; color: white; padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        download_btn.clicked.connect(self._start_download)
        button_layout.addWidget(download_btn)
        
        layout.addLayout(button_layout)
        
        # Note
        note = self.QLabel("💡 You can download the model later from settings.")
        note.setStyleSheet("color: #999; font-size: 12px; margin-top: 10px;")
        layout.addWidget(note)
        
        self.dialog.setLayout(layout)
        
        result = self.dialog.exec_()
        return result == self.QDialog.Accepted
    
    def _start_download(self):
        """Start download process"""
        self.is_downloading = True
        
        # Hide buttons, show progress
        for btn in self.dialog.findChildren(self.QPushButton):
            btn.setEnabled(False)
        
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        
        # Set progress callback
        self.handler.set_progress_callback(self.update_progress)
        
        # Start download in thread
        try:
            self.handler.download_model_async()
            
            # Wait for download to complete
            while self.handler.download_thread.is_alive():
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                time.sleep(0.1)
            
            self.show_success()
            self.dialog.accept()
            
        except Exception as e:
            self.show_error(str(e))
            self.is_downloading = False
            for btn in self.dialog.findChildren(self.QPushButton):
                btn.setEnabled(True)
    
    def update_progress(self, current: int, total: int):
        """Update progress display"""
        if self.progress_bar:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            
            mb_current = current / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(f"Downloading: {mb_current:.1f} MB / {mb_total:.1f} MB ({percent}%)")
    
    def show_success(self):
        """Show success message"""
        self.QMessageBox.information(
            self.dialog,
            "Success",
            "Model downloaded successfully!\nYou can now use FarmIntel offline."
        )
    
    def show_error(self, error: str):
        """Show error message"""
        self.QMessageBox.critical(
            self.dialog,
            "Download Failed",
            f"Failed to download model:\n{error}"
        )


def check_and_download_model(app_dir: str = None, use_gui: bool = True) -> str:
    """
    Check if model is downloaded, show download dialog if needed
    Returns path to model file
    """
    handler = ModelDownloadHandler(app_dir)
    
    # Check if already downloaded
    if handler.is_model_downloaded():
        print(f"✓ Model found at {handler.get_model_path()}")
        return handler.get_model_path()
    
    print("Model not found. Starting download...")
    
    if use_gui:
        try:
            ui = PyQt5ModelDownloadUI(handler)
            if ui.show_download_dialog():
                return handler.get_model_path()
            else:
                print("Download skipped by user")
                return None
        except ImportError:
            print("PyQt5 not available, using CLI download")
            use_gui = False
    
    if not use_gui:
        # CLI download
        print(f"Downloading model from {handler.MODEL_URL}...")
        handler.download_model_async().join()
        return handler.get_model_path()


if __name__ == '__main__':
    # Test the download handler
    handler = ModelDownloadHandler()
    
    if handler.is_model_downloaded():
        print(f"✓ Model already downloaded at {handler.get_model_path()}")
    else:
        print("Model not found. Downloading...")
        
        def progress_callback(current, total):
            percent = (current / total) * 100
            mb_current = current / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            print(f"Progress: {mb_current:.1f} MB / {mb_total:.1f} MB ({percent:.1f}%)", end='\r')
        
        handler.set_progress_callback(progress_callback)
        handler.download_model_async().join()
        print(f"\n✓ Model downloaded to {handler.get_model_path()}")
