"""
Hybrid Mode Handler - Seamlessly switches between online and offline
Provides fallback when network is unavailable
Uses local LLM for offline inference
"""

import json
import requests
from typing import Dict, Optional
from offline_router import OfflineRouter, OfflineResponseGenerator
from cache_manager import OfflineCacheManager
from local_llm import get_local_llm

class HybridModeHandler:
    """Handle online/offline switching with automatic fallback"""
    
    def __init__(self, online_api_url: str, cache_dir: str = './offline_cache', model_path: str = None):
        self.online_api_url = online_api_url
        self.cache = OfflineCacheManager(cache_dir)
        self.router = OfflineRouter(self.cache)
        self.response_gen = OfflineResponseGenerator(self.cache)
        self.llm = get_local_llm(model_path)
        self.timeout = 5  # seconds
        
        # Log LLM status
        if self.llm.is_available():
            print("[INFO] Local LLM is available for offline inference")
        else:
            print("[WARNING] Local LLM not available, using rule-based responses")
    
    def process_query(self, query: str, conversation_history: list = None) -> Dict:
        """
        Process query with automatic online/offline fallback
        
        Returns:
            {
                'response': str,
                'mode': 'online' | 'offline',
                'context': dict,
                'cached': bool
            }
        """
        
        # Try online first
        online_result = self._try_online(query, conversation_history)
        if online_result:
            return online_result
        
        # Fallback to offline
        return self._handle_offline(query)
    
    def _try_online(self, query: str, conversation_history: list = None) -> Optional[Dict]:
        """Try to get response from online API"""
        try:
            payload = {
                'query': query,
                'language': 'en',
                'conversation_history': conversation_history or []
            }
            
            response = requests.post(
                f"{self.online_api_url}/api/llm/query",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the response data if it contains prices/insights
                if 'context' in data:
                    self._cache_response_data(data['context'])
                
                return {
                    'response': data.get('response', ''),
                    'mode': 'online',
                    'context': data.get('context', {}),
                    'cached': False
                }
        except (requests.ConnectionError, requests.Timeout, requests.RequestException):
            pass
        
        return None
    
    def _handle_offline(self, query: str) -> Dict:
        """Handle query in offline mode"""
        
        # Route the query
        routing = self.router.route(query)
        
        # Get appropriate handler
        handler_name = routing['handler']
        handler = getattr(self.response_gen, handler_name, None)
        
        if not handler:
            response = self.response_gen.handle_general_query(routing['crop'], query)
        else:
            response = handler(routing['crop'], query)
        
        return {
            'response': response,
            'mode': 'offline',
            'context': {
                'crop': routing['crop'],
                'query_type': routing['query_type'],
                'cached': True
            },
            'cached': True
        }
    
    def _cache_response_data(self, context: Dict):
        """Cache prices and insights from online response"""
        try:
            if 'prices' in context:
                crop = context.get('crop')
                if crop:
                    self.cache.save_prices(crop, context['prices'])
            
            if 'insights' in context:
                crop = context.get('crop')
                if crop:
                    self.cache.save_insights(crop, context['insights'])
        except Exception as e:
            print(f"Error caching response data: {e}")
    
    def get_cache_status(self) -> Dict:
        """Get current cache status"""
        stats = self.cache.get_cache_stats()
        return {
            'mode': 'hybrid',
            'cache_available': len(stats.get('crops_available', [])) > 0,
            'stats': stats
        }
    
    def prefetch_data(self, crops: list) -> Dict:
        """
        Prefetch data for specified crops to improve offline experience
        Call this when online to prepare for offline use
        """
        results = {
            'prefetched_crops': [],
            'failed_crops': [],
            'total_size_mb': 0
        }
        
        for crop in crops:
            try:
                payload = {
                    'query': f'What is the price of {crop}?',
                    'conversation_history': []
                }
                
                response = requests.post(
                    f"{self.online_api_url}/api/llm/query",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'context' in data:
                        self._cache_response_data(data['context'])
                        results['prefetched_crops'].append(crop)
            except Exception as e:
                print(f"Error prefetching data for {crop}: {e}")
                results['failed_crops'].append(crop)
        
        stats = self.cache.get_cache_stats()
        results['total_size_mb'] = stats.get('cache_size_mb', 0)
        
        return results


class OfflineIndicator:
    """Provide UI indicators for offline/online status"""
    
    @staticmethod
    def get_status_badge(mode: str, cached: bool) -> Dict:
        """Get status badge for UI"""
        if mode == 'online':
            return {
                'text': '🟢 Online',
                'color': '#10a37f',
                'tooltip': 'Connected to server'
            }
        elif cached:
            return {
                'text': '🟡 Offline (Cached)',
                'color': '#f59e0b',
                'tooltip': 'Using cached data'
            }
        else:
            return {
                'text': '🔴 Offline',
                'color': '#ef4444',
                'tooltip': 'No internet connection'
            }
    
    @staticmethod
    def get_response_metadata(result: Dict) -> str:
        """Get metadata string for response"""
        mode = result.get('mode', 'unknown')
        cached = result.get('cached', False)
        
        if mode == 'online':
            return "✓ Real-time data from server"
        elif cached:
            return "⚠ Using cached data (offline mode)"
        else:
            return "⚠ Limited offline response"
