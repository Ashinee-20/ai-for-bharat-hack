"""
Setup script for offline model
Helps move/copy the TinyLlama model to the correct location
"""

import os
import shutil
from pathlib import Path


def find_model():
    """Find the TinyLlama model file"""
    print("\n" + "="*70)
    print("  Searching for TinyLlama Model")
    print("="*70)
    
    possible_locations = [
        "D:\\MY Orgs\\ai-for-bharat-hack\\tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
        "D:\\MY Orgs\\ai-for-bharat-hack\\farmintel-v1\\tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
        "tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
        "../tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
        "../../tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf",
    ]
    
    print("\nSearching in:")
    for location in possible_locations:
        print(f"  - {location}")
        if os.path.exists(location):
            print(f"    ✓ FOUND!")
            return location
    
    print("\n✗ Model not found in any location")
    return None


def copy_model_to_farmintel():
    """Copy model to farmintel-v1 directory"""
    model_path = find_model()
    
    if not model_path:
        print("\n[ERROR] Could not find model file")
        print("\nPlease ensure the model is at:")
        print("  D:\\MY Orgs\\ai-for-bharat-hack\\tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf")
        return False
    
    # Destination
    dest_dir = Path(__file__).parent
    dest_path = dest_dir / "tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf"
    
    print("\n" + "="*70)
    print("  Copying Model")
    print("="*70)
    
    print(f"\nSource: {model_path}")
    print(f"Destination: {dest_path}")
    
    # Check if already exists
    if dest_path.exists():
        print(f"\n✓ Model already exists at destination")
        print(f"  Size: {dest_path.stat().st_size / (1024*1024):.1f} MB")
        return True
    
    # Copy file
    try:
        print(f"\nCopying... (this may take a minute)")
        shutil.copy2(model_path, dest_path)
        
        size_mb = dest_path.stat().st_size / (1024*1024)
        print(f"✓ Model copied successfully!")
        print(f"  Size: {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"✗ Error copying model: {e}")
        return False


def verify_setup():
    """Verify the setup"""
    print("\n" + "="*70)
    print("  Verifying Setup")
    print("="*70)
    
    # Check model file
    model_path = Path(__file__).parent / "tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf"
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024*1024)
        print(f"\n✓ Model file exists")
        print(f"  Path: {model_path}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print(f"\n✗ Model file not found at {model_path}")
        return False
    
    # Check offline directory
    offline_dir = Path(__file__).parent / "offline"
    if offline_dir.exists():
        print(f"\n✓ Offline directory exists")
        print(f"  Path: {offline_dir}")
        
        # Check key files
        key_files = [
            "local_llm.py",
            "offline_router.py",
            "hybrid_mode.py",
            "cache_manager.py",
            "requirements.txt",
            "test_offline_llm.py",
            "test_interactive.py",
        ]
        
        for file in key_files:
            file_path = offline_dir / file
            if file_path.exists():
                print(f"    ✓ {file}")
            else:
                print(f"    ✗ {file} (missing)")
    else:
        print(f"\n✗ Offline directory not found")
        return False
    
    return True


def test_llm():
    """Test if LLM can be loaded"""
    print("\n" + "="*70)
    print("  Testing LLM Loading")
    print("="*70)
    
    try:
        from offline.local_llm import get_local_llm
        
        print("\nLoading LLM...")
        llm = get_local_llm()
        
        if llm.is_available():
            print("✓ LLM loaded successfully!")
            
            # Try a simple generation
            print("\nTesting inference...")
            response = llm.generate("Hello", max_tokens=20)
            if response:
                print(f"✓ Inference successful!")
                print(f"  Response: {response[:50]}...")
                return True
            else:
                print("✗ Inference failed (no response)")
                return False
        else:
            print("✗ LLM not available")
            print("\nMake sure llama-cpp-python is installed:")
            print("  pip install llama-cpp-python")
            return False
    except Exception as e:
        print(f"✗ Error testing LLM: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main setup function"""
    print("\n╔" + "="*68 + "╗")
    print("║" + " "*20 + "FarmIntel Offline Model Setup" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    
    # Step 1: Copy model
    print("\n[Step 1/3] Copying model to farmintel-v1...")
    if not copy_model_to_farmintel():
        print("\n[ERROR] Failed to copy model")
        return False
    
    # Step 2: Verify setup
    print("\n[Step 2/3] Verifying setup...")
    if not verify_setup():
        print("\n[ERROR] Setup verification failed")
        return False
    
    # Step 3: Test LLM
    print("\n[Step 3/3] Testing LLM...")
    if not test_llm():
        print("\n[ERROR] LLM test failed")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r offline/requirements.txt")
        print("2. Check model file exists and is readable")
        print("3. Check llama-cpp-python is installed correctly")
        return False
    
    # Success
    print("\n" + "="*70)
    print("  ✓ SETUP COMPLETE!")
    print("="*70)
    
    print("\nYou can now:")
    print("1. Run interactive tests:")
    print("   python offline/test_interactive.py")
    print("\n2. Run automated tests:")
    print("   python offline/test_offline_llm.py")
    print("\n3. Try examples:")
    print("   python offline/example_usage.py")
    print("\n4. Integrate with your app:")
    print("   from offline.hybrid_mode import HybridModeHandler")
    print("   handler = HybridModeHandler('https://your-api.com')")
    print("   result = handler.process_query('What is the price of wheat?')")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
