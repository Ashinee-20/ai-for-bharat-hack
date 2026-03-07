"""
FarmIntel Desktop Application
Main entry point with model download on first run
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from model_download_handler import check_and_download_model


def main():
    """Main application entry point"""
    
    # Get app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check and download model if needed
    print("=" * 60)
    print("FarmIntel Desktop Application")
    print("=" * 60)
    
    model_path = check_and_download_model(app_dir, use_gui=True)
    
    if not model_path:
        print("\n⚠️  Model download is required to use offline features.")
        print("You can download it later from the settings menu.")
        print("\nStarting FarmIntel in online-only mode...")
    else:
        print(f"\n✓ Model ready at: {model_path}")
        print("Starting FarmIntel with offline support...")
    
    # Import and start GUI
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow(model_path=model_path)
        window.show()
        
        sys.exit(app.exec_())
        
    except ImportError:
        print("\n✗ PyQt5 is required for the GUI.")
        print("Install it with: pip install PyQt5")
        print("\nStarting in CLI mode instead...")
        
        # CLI mode
        from offline.offline_router import OfflineRouter
        from offline.local_llm import LocalLLMManager
        
        if model_path:
            llm = LocalLLMManager(model_path)
            router = OfflineRouter(llm)
            
            print("\n" + "=" * 60)
            print("FarmIntel CLI - Offline Mode")
            print("=" * 60)
            print("Type 'quit' to exit\n")
            
            while True:
                try:
                    query = input("You: ").strip()
                    if query.lower() in ['quit', 'exit', 'q']:
                        print("Goodbye!")
                        break
                    
                    if not query:
                        continue
                    
                    response = router.route_query(query)
                    print(f"\nFarmIntel: {response}\n")
                    
                except KeyboardInterrupt:
                    print("\n\nGoodbye!")
                    break
                except Exception as e:
                    print(f"Error: {e}\n")
        else:
            print("Model not available. Please download it first.")


if __name__ == '__main__':
    main()
