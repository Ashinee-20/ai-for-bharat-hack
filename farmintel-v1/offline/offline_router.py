"""
Offline Router - Routes queries and generates responses using local LLM
Uses skill taxonomy from llm_service for consistent guidance
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional
from local_llm import get_local_llm
from cache_manager import OfflineCacheManager

# Import skills from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent / 'lambda'))
try:
    from llm_service import SKILLS, identify_skill, get_skill_context
except ImportError:
    # Fallback if import fails
    SKILLS = {}
    def identify_skill(query):
        return None
    def get_skill_context(skill):
        return ""


class OfflineRouter:
    """Route queries in offline mode using skill taxonomy"""
    
    def __init__(self, cache: OfflineCacheManager):
        self.cache = cache
        self.llm = get_local_llm()
        self.skills = SKILLS  # Use skills from llm_service
        
        # Crop keywords for routing
        self.crops = {
            'wheat': ['wheat', 'गेहूं'],
            'rice': ['rice', 'चावल'],
            'tomato': ['tomato', 'टमाटर'],
            'potato': ['potato', 'आलू'],
            'onion': ['onion', 'प्याज'],
            'cotton': ['cotton', 'कपास'],
            'sugarcane': ['sugarcane', 'गन्ना'],
            'maize': ['maize', 'मक्का'],
            'chilli': ['chilli', 'मिर्च'],
            'cabbage': ['cabbage', 'गोभी'],
        }
        
        # Query type keywords
        self.query_types = {
            'price': ['price', 'cost', 'rate', 'mandi', 'market', 'sell', 'buy', 'भाव', 'दाम'],
            'weather': ['weather', 'rain', 'temperature', 'humidity', 'wind', 'मौसम', 'बारिश'],
            'soil': ['soil', 'ph', 'nitrogen', 'phosphorus', 'nutrient', 'मिट्टी', 'उर्वरता'],
            'pest': ['pest', 'insect', 'bug', 'aphid', 'whitefly', 'कीट', 'कीड़े'],
            'disease': ['disease', 'fungal', 'bacterial', 'blight', 'wilt', 'रोग', 'बीमारी'],
            'irrigation': ['water', 'irrigation', 'drip', 'drought', 'सिंचाई', 'पानी'],
            'fertilizer': ['fertilizer', 'manure', 'compost', 'npk', 'खाद', 'जैव'],
            'harvest': ['harvest', 'reap', 'storage', 'post-harvest', 'कटाई', 'भंडारण'],
        }
    
    def route(self, query: str) -> Dict:
        """
        Route query to appropriate handler using skill taxonomy
        
        Returns:
            {
                'crop': str,
                'query_type': str,
                'handler': str,
                'skill': str,
                'skill_context': str,
                'confidence': float
            }
        """
        query_lower = query.lower()
        
        # Identify crop
        crop = self._identify_crop(query_lower)
        
        # Identify query type
        query_type = self._identify_query_type(query_lower)
        
        # Identify skill using llm_service function
        skill = identify_skill(query)
        skill_context = get_skill_context(skill) if skill else ""
        
        # Determine handler
        handler = f"handle_{query_type}"
        
        return {
            'crop': crop,
            'query_type': query_type,
            'handler': handler,
            'skill': skill,
            'skill_context': skill_context,
            'confidence': 0.8
        }
    
    def _identify_crop(self, query: str) -> Optional[str]:
        """Identify crop from query"""
        for crop, keywords in self.crops.items():
            for keyword in keywords:
                if keyword in query:
                    return crop
        return None
    
    def _identify_query_type(self, query: str) -> str:
        """Identify query type from keywords"""
        for qtype, keywords in self.query_types.items():
            for keyword in keywords:
                if keyword in query:
                    return qtype
        return 'general'


class OfflineResponseGenerator:
    """Generate responses in offline mode using skills"""
    
    def __init__(self, cache: OfflineCacheManager):
        self.cache = cache
        self.llm = get_local_llm()
        self.skills = SKILLS
    
    def generate_with_skill(self, query: str, skill: str, skill_context: str) -> str:
        """Generate response using skill context"""
        if not self.llm.is_available():
            return ""
        
        # Build prompt with skill guidelines
        prompt = f"""You are providing {skill.replace('_', ' ').title()} advice.

{skill_context}

User question: {query}

Provide practical, concise advice."""
        
        return self.llm.generate(prompt, max_tokens=150)
    
    def handle_price(self, crop: str, query: str, skill_context: str = "") -> str:
        """Handle price queries"""
        if not crop:
            return "कृपया बताएं कि आप किस फसल के बारे में पूछ रहे हैं (जैसे गेहूं, चावल, टमाटर)।"
        
        # Try to get cached prices
        prices = self.cache.get_prices(crop)
        
        if prices:
            response = f"**{crop.capitalize()} के मंडी भाव (कैश्ड डेटा)**\n\n"
            response += "| मंडी | भाव (₹) | राज्य |\n"
            response += "|-------|-----------|-------|\n"
            
            for price in prices[:5]:
                response += f"| {price['mandi']} | {price['price']} | {price['state']} |\n"
            
            response += f"\n*अंतिम अपडेट: {prices[0]['date']}*\n"
            response += "*नोट: यह कैश्ड डेटा है। वर्तमान भाव के लिए इंटरनेट से जुड़ें।*"
            return response
        
        # Use LLM to generate response
        if self.llm.is_available():
            prompt = f"Provide general price guidance for {crop} in India. Keep it brief."
            return self.llm.generate(prompt, max_tokens=100)
        
        return f"कोई कैश्ड डेटा नहीं है {crop} के लिए। कृपया इंटरनेट से जुड़ें।"
    
    def handle_weather(self, crop: str, query: str) -> str:
        """Handle weather queries"""
        if self.llm.is_available():
            prompt = f"Provide weather advisory for farming. Keep it brief and practical."
            return self.llm.generate(prompt, max_tokens=100)
        
        return """**मौसम सलाह (ऑफलाइन मोड)**

**सामान्य सुझाव:**
- अधिकांश फसलों को 20-30°C तापमान की आवश्यकता होती है
- चरम गर्मी या ठंड के दौरान रोपण से बचें
- सिंचाई योजना के लिए वर्षा की निगरानी करें"""
    
    def handle_soil(self, crop: str, query: str) -> str:
        """Handle soil queries"""
        if self.llm.is_available():
            prompt = f"""Answer this soil management question briefly in 2-3 sentences:
{query}
Crop: {crop if crop else 'general'}

Answer:"""
            return self.llm.generate(prompt, max_tokens=100)
        
        return """**मिट्टी सलाह (ऑफलाइन मोड)**

**अम्लीय मिट्टी (pH < 6.5):**
- चूना या लकड़ी की राख डालें (2-3 टन/हेक्टेयर)

**क्षारीय मिट्टी (pH > 8.0):**
- गंधक या जिप्सम डालें (1-2 टन/हेक्टेयर)

**कम नाइट्रोजन:**
- खाद या गोबर डालें (5-10 टन/हेक्टेयर)"""
    
    def handle_pest(self, crop: str, query: str) -> str:
        """Handle pest queries"""
        if self.llm.is_available():
            prompt = f"""Answer this pest management question briefly in 2-3 sentences:
{query}
Crop: {crop if crop else 'general'}

Answer:"""
            return self.llm.generate(prompt, max_tokens=100)
        
        return """Pest Management (Offline Mode)

Common Pests & Organic Control:

Aphids: Spray neem oil (3%) or use soap spray
Whiteflies: Yellow sticky traps or neem spray
Caterpillars: Hand-pick or use Bt spray
Mites: Sulfur dust or neem oil spray

For chemical pesticides, connect to internet for recommendations."""
    
    def handle_disease(self, crop: str, query: str) -> str:
        """Handle disease queries"""
        if self.llm.is_available():
            prompt = f"Provide disease management for {crop}. Keep it brief."
            return self.llm.generate(prompt, max_tokens=100)
        
        return """**रोग प्रबंधन (ऑफलाइन मोड)**

**पीली पत्तियां:** नाइट्रोजन की कमी या फंगल संक्रमण
**भूरे धब्बे:** संभवतः फंगल संक्रमण - प्रभावित भागों को हटाएं
**मुरझाना:** मिट्टी की नमी जांचें, जड़ सड़न हो सकता है"""
    
    def handle_irrigation(self, crop: str, query: str) -> str:
        """Handle irrigation queries"""
        if self.llm.is_available():
            prompt = f"""Answer this irrigation question briefly in 2-3 sentences:
{query}
Crop: {crop if crop else 'general'}

Answer:"""
            return self.llm.generate(prompt, max_tokens=100)
        
        return """Irrigation Advisory (Offline Mode)

General Water Requirements:
- Cereals: 40-60 cm per season
- Vegetables: 30-50 cm per season
- Fruits: 60-100 cm per season

Irrigation Frequency:
- Summer: Every 7-10 days
- Winter: Every 15-20 days

Check soil moisture: Squeeze soil - if it crumbles, water needed"""
    
    def handle_fertilizer(self, crop: str, query: str) -> str:
        """Handle fertilizer queries"""
        if self.llm.is_available():
            prompt = f"Provide fertilizer recommendations for {crop}. Keep it brief."
            return self.llm.generate(prompt, max_tokens=100)
        
        return """**खाद सलाह (ऑफलाइन मोड)**

**जैविक खाद:**
- कंपोस्ट: 5-10 टन/हेक्टेयर
- वर्मीकंपोस्ट: 2-5 टन/हेक्टेयर
- गोबर: 10-15 टन/हेक्टेयर

**NPK अनुपात:**
- पूर्व-रोपण: 10:26:26
- वनस्पति: 20:20:20
- फूल: 10:52:10"""
    
    def handle_harvest(self, crop: str, query: str) -> str:
        """Handle harvest queries"""
        if self.llm.is_available():
            prompt = f"""Answer this harvest question briefly in 2-3 sentences:
{query}
Crop: {crop if crop else 'general'}

Answer:"""
            return self.llm.generate(prompt, max_tokens=100)
        
        return """Harvest Advisory (Offline Mode)

General Harvest Indicators:
- Cereals: When grain is hard and doesn't dent
- Vegetables: Pick at proper maturity
- Fruits: When fully colored and slightly soft

Post-Harvest Storage:
- Dry grains to 12-14% moisture
- Store in cool, dry place
- Use airtight containers"""
    
    def handle_general(self, crop: str, query: str) -> str:
        """Handle general queries"""
        if self.llm.is_available():
            prompt = f"Provide agricultural advice. Query: {query}. Keep it brief."
            return self.llm.generate(prompt, max_tokens=100)
        
        return """**सामान्य कृषि सलाह (ऑफलाइन मोड)**

मैं वर्तमान में ऑफलाइन मोड में हूं।

**मैं ऑफलाइन में मदद कर सकता हूं:**
- कैश्ड फसल भाव
- सामान्य कृषि सुझाव
- कीट और रोग प्रबंधन
- मिट्टी और सिंचाई सलाह

**वर्तमान डेटा के लिए इंटरनेट से जुड़ें।"""
