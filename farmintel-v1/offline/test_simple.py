"""
Simple Interactive Test for Offline LLM
No Unicode characters - Windows compatible
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'lambda'))

from local_llm import get_local_llm
from cache_manager import OfflineCacheManager
from offline_router import OfflineRouter, OfflineResponseGenerator

try:
    from llm_service import identify_skill, get_skill_context
except ImportError:
    print("[WARNING] Could not import skills from llm_service")
    def identify_skill(q):
        return None
    def get_skill_context(s):
        return ""


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print("  " + text)
    print("="*70)


def test_llm():
    """Test if local LLM is available"""
    print_header("TEST 1: Local LLM Availability")
    
    llm = get_local_llm()
    
    if llm.is_available():
        print("[OK] Local LLM is AVAILABLE")
        print("     Model path: " + str(llm.model_path))
        return True
    else:
        print("[ERROR] Local LLM is NOT available")
        return False


def test_skills():
    """Test skill detection"""
    print_header("TEST 2: Skill Detection")
    
    test_queries = [
        "What is the price of wheat?",
        "How much water does rice need?",
        "How to prevent pest damage?",
        "What about soil pH?",
    ]
    
    print("\nDetecting skills for queries:\n")
    
    for query in test_queries:
        skill = identify_skill(query)
        print("Query: " + query)
        print("Skill: " + (skill if skill else "None"))
        print()


def test_routing():
    """Test query routing"""
    print_header("TEST 3: Query Routing")
    
    cache = OfflineCacheManager('./offline_cache')
    router = OfflineRouter(cache)
    
    test_queries = [
        "What is the price of wheat?",
        "How much water does rice need?",
        "How to prevent pest damage?",
    ]
    
    print("\nRouting queries:\n")
    
    for query in test_queries:
        routing = router.route(query)
        print("Query: " + query)
        print("  Crop: " + str(routing['crop']))
        print("  Type: " + routing['query_type'])
        print("  Skill: " + str(routing['skill']))
        print()


def test_responses():
    """Test response generation"""
    print_header("TEST 4: Response Generation")
    
    cache = OfflineCacheManager('./offline_cache')
    gen = OfflineResponseGenerator(cache)
    
    test_queries = [
        ("What is the price of wheat?", "price"),
        ("How much water does rice need?", "irrigation"),
        ("How to prevent pest damage?", "pest"),
    ]
    
    print("\nGenerating responses:\n")
    
    for query, qtype in test_queries:
        print("Query: " + query)
        print("Type: " + qtype)
        
        # Generate response
        if qtype == "price":
            response = gen.handle_price(None, query)
        elif qtype == "irrigation":
            response = gen.handle_irrigation(None, query)
        elif qtype == "pest":
            response = gen.handle_pest(None, query)
        else:
            response = gen.handle_general(None, query)
        
        print("Response: " + response[:100] + "...")
        print()


def interactive_mode():
    """Interactive Q&A mode"""
    print_header("INTERACTIVE MODE")
    
    print("\nEnter your agricultural questions (type 'quit' to exit)")
    print("Examples:")
    print("  - What is the price of wheat?")
    print("  - How much water does rice need?")
    print("  - How to prevent pest damage?")
    
    cache = OfflineCacheManager('./offline_cache')
    router = OfflineRouter(cache)
    gen = OfflineResponseGenerator(cache)
    
    while True:
        print("\n" + "-"*70)
        query = input("You: ").strip()
        
        if query.lower() == 'quit':
            print("\nExiting...")
            break
        
        if not query:
            print("Please enter a question")
            continue
        
        # Route the query
        routing = router.route(query)
        
        print("\n[Analysis]")
        print("  Crop: " + str(routing['crop']))
        print("  Query Type: " + routing['query_type'])
        print("  Skill: " + str(routing['skill']))
        
        # Generate response
        handler_name = routing['handler']
        handler = getattr(gen, handler_name, None)
        
        if handler:
            response = handler(routing['crop'], query)
        else:
            response = gen.handle_general(routing['crop'], query)
        
        print("\n[Response]")
        print("FarmIntel: " + response)


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  FarmIntel Offline LLM - Simple Interactive Test")
    print("="*70)
    
    # Test 1: LLM Availability
    llm_available = test_llm()
    
    if not llm_available:
        print("\n[ERROR] Local LLM not available. Cannot proceed.")
        print("\nTo fix:")
        print("1. Install llama-cpp-python: pip install llama-cpp-python")
        print("2. Ensure model file exists")
        return
    
    # Test 2: Skill Detection
    test_skills()
    
    # Test 3: Query Routing
    test_routing()
    
    # Test 4: Response Generation
    test_responses()
    
    # Interactive Mode
    print_header("INTERACTIVE MODE")
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print("\nError: " + str(e))
        import traceback
        traceback.print_exc()
    
    print_header("TEST COMPLETE")
    print("\n[OK] All tests completed!")


if __name__ == "__main__":
    main()
