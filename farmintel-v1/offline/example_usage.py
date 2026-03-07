"""
Example usage of FarmIntel Offline LLM Integration
Shows different ways to use the offline system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from local_llm import get_local_llm
from hybrid_mode import HybridModeHandler
from cache_manager import OfflineCacheManager
from offline_router import OfflineRouter, OfflineResponseGenerator


def example_1_basic_llm():
    """Example 1: Basic LLM usage"""
    print("\n" + "="*60)
    print("Example 1: Basic LLM Usage")
    print("="*60)
    
    llm = get_local_llm()
    
    if not llm.is_available():
        print("Local LLM not available. Install with: pip install llama-cpp-python")
        return
    
    # Generate response
    prompt = "What is the best time to plant wheat in India?"
    response = llm.generate(prompt, max_tokens=100)
    
    print(f"\nPrompt: {prompt}")
    print(f"Response: {response}")


def example_2_chat_mode():
    """Example 2: Chat mode"""
    print("\n" + "="*60)
    print("Example 2: Chat Mode")
    print("="*60)
    
    llm = get_local_llm()
    
    if not llm.is_available():
        print("Local LLM not available")
        return
    
    # Chat conversation
    messages = [
        {"role": "system", "content": "You are a helpful farming assistant."},
        {"role": "user", "content": "How do I prevent pest damage on my wheat crop?"}
    ]
    
    response = llm.chat(messages, max_tokens=100)
    
    print(f"\nUser: How do I prevent pest damage on my wheat crop?")
    print(f"Assistant: {response}")


def example_3_hybrid_mode():
    """Example 3: Hybrid mode (online/offline)"""
    print("\n" + "="*60)
    print("Example 3: Hybrid Mode (Online/Offline)")
    print("="*60)
    
    # Initialize hybrid handler
    handler = HybridModeHandler(
        online_api_url="http://localhost:3000",  # Your API URL
        cache_dir='./offline_cache'
    )
    
    # Process query (tries online first, falls back to offline)
    queries = [
        "What is the price of wheat?",
        "How much water does rice need?",
        "How to prevent pest damage?",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        result = handler.process_query(query)
        
        print(f"Mode: {result['mode']}")
        print(f"Cached: {result['cached']}")
        print(f"Response: {result['response'][:100]}...")


def example_4_offline_router():
    """Example 4: Offline router"""
    print("\n" + "="*60)
    print("Example 4: Offline Router")
    print("="*60)
    
    cache = OfflineCacheManager('./offline_cache')
    router = OfflineRouter(cache)
    gen = OfflineResponseGenerator(cache)
    
    # Test different query types
    queries = [
        ("What is the price of wheat?", "price"),
        ("How much water does rice need?", "irrigation"),
        ("How to prevent pest damage?", "pest"),
        ("What about soil pH?", "soil"),
        ("When to harvest?", "harvest"),
    ]
    
    for query, expected_type in queries:
        print(f"\nQuery: {query}")
        
        # Route the query
        routing = router.route(query)
        print(f"  Detected Type: {routing['query_type']} (expected: {expected_type})")
        print(f"  Crop: {routing['crop']}")
        print(f"  Handler: {routing['handler']}")
        
        # Generate response
        handler_name = routing['handler']
        handler = getattr(gen, handler_name, None)
        
        if handler:
            response = handler(routing['crop'], query)
            print(f"  Response: {response[:80]}...")


def example_5_cache_management():
    """Example 5: Cache management"""
    print("\n" + "="*60)
    print("Example 5: Cache Management")
    print("="*60)
    
    cache = OfflineCacheManager('./offline_cache')
    
    # Save sample prices
    sample_prices = [
        {
            'mandi': 'Azadpur Mandi',
            'state': 'Delhi',
            'district': 'Delhi',
            'price': 2500,
            'min_price': 2400,
            'max_price': 2600,
            'date': '2026-03-07',
            'variety': 'PBW 343'
        },
        {
            'mandi': 'Nagpur APMC',
            'state': 'Maharashtra',
            'district': 'Nagpur',
            'price': 2600,
            'min_price': 2500,
            'max_price': 2700,
            'date': '2026-03-07',
            'variety': 'HD 2967'
        }
    ]
    
    print("\nSaving prices to cache...")
    cache.save_prices('wheat', sample_prices)
    print("✓ Prices saved")
    
    # Retrieve prices
    print("\nRetrieving prices from cache...")
    prices = cache.get_prices('wheat')
    if prices:
        print(f"✓ Retrieved {len(prices)} prices:")
        for p in prices:
            print(f"  - {p['mandi']}: ₹{p['price']} ({p['state']})")
    
    # Get cache stats
    print("\nCache statistics:")
    stats = cache.get_cache_stats()
    print(f"  Cached prices: {stats['cached_prices']}")
    print(f"  Cached insights: {stats['cached_insights']}")
    print(f"  Available crops: {stats['crops_available']}")
    print(f"  Cache size: {stats['cache_size_mb']:.2f}MB")


def example_6_multilingual():
    """Example 6: Multilingual support"""
    print("\n" + "="*60)
    print("Example 6: Multilingual Support")
    print("="*60)
    
    cache = OfflineCacheManager('./offline_cache')
    router = OfflineRouter(cache)
    gen = OfflineResponseGenerator(cache)
    
    # English query
    print("\nEnglish Query:")
    query_en = "What is the price of wheat?"
    routing = router.route(query_en)
    print(f"Query: {query_en}")
    print(f"Type: {routing['query_type']}")
    
    # Hindi query
    print("\nHindi Query:")
    query_hi = "गेहूं की कीमत क्या है?"
    routing = router.route(query_hi)
    print(f"Query: {query_hi}")
    print(f"Type: {routing['query_type']}")
    
    # Generate response
    response = gen.handle_price('wheat', query_hi)
    print(f"Response: {response[:100]}...")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("FarmIntel Offline LLM - Usage Examples")
    print("="*60)
    
    examples = [
        ("Basic LLM Usage", example_1_basic_llm),
        ("Chat Mode", example_2_chat_mode),
        ("Hybrid Mode", example_3_hybrid_mode),
        ("Offline Router", example_4_offline_router),
        ("Cache Management", example_5_cache_management),
        ("Multilingual Support", example_6_multilingual),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n❌ Example {i} ({name}) failed:")
            print(f"   {str(e)}")
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
