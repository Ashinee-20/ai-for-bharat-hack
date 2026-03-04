"""
LLM Service - Groq Integration with AWS Bedrock Fallback
Uses Groq Llama 3.3 70B (fast, high limits) for conversational AI
Falls back to AWS Bedrock (Amazon Nova Lite) if Groq fails
"""
import json
import os
import boto3
import urllib3

# Initialize boto3 clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
ssm = boto3.client('ssm', region_name='ap-south-1')  # Same region as Lambda

BEDROCK_MODEL = os.environ.get('BEDROCK_MODEL_ID', 'us.amazon.nova-lite-v1:0')

# Groq configuration (fallback)
GROQ_MODEL = 'llama-3.3-70b-versatile'
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

# HTTP client for Groq API
http = urllib3.PoolManager()

# Cache for Groq API key
_groq_api_key_cache = None

def get_groq_api_key():
    """
    Get Groq API key from Parameter Store (cached)
    """
    global _groq_api_key_cache
    
    if _groq_api_key_cache:
        return _groq_api_key_cache
    
    try:
        response = ssm.get_parameter(
            Name='/farmintel/groq-api-key',
            WithDecryption=True
        )
        _groq_api_key_cache = response['Parameter']['Value']
        return _groq_api_key_cache
    except Exception as e:
        print(f"Error fetching Groq API key from Parameter Store: {e}")
        # Fallback to environment variable (for local testing)
        return os.environ.get('GROQ_API_KEY', '')

def lambda_handler(event, context):
    """
    Main handler for LLM queries
    """
    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Cache-Control,Pragma,Expires',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    body = json.loads(event.get('body', '{}'))
    
    query = body.get('query', '')
    context_data = body.get('context', {})
    language = body.get('language', 'en')
    
    if not query:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Cache-Control,Pragma,Expires'
            },
            'body': json.dumps({'error': 'Query is required'})
        }
    
    # Auto-fetch price data if query mentions crops or prices
    if not context_data or 'prices' not in context_data:
        context_data = auto_fetch_context(query)
    
    response, model_used = generate_response(query, context_data, language)
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Cache-Control,Pragma,Expires',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps({
            'response': response,
            'model': model_used
        })
    }

def auto_fetch_context(query):
    """
    Use LLM to decide what data to fetch, then fetch it
    """
    query_lower = query.lower()
    crops = ['wheat', 'rice', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane']
    
    # Find which crop is mentioned
    mentioned_crop = None
    for crop in crops:
        if crop in query_lower:
            mentioned_crop = crop
            break
    
    if not mentioned_crop:
        return {}
    
    context = {'crop': mentioned_crop}
    
    # Determine what data is needed based on query keywords
    needs_prices = any(word in query_lower for word in ['price', 'cost', 'rate', 'how much', 'rupee', '₹', 'mandi'])
    needs_insights = any(word in query_lower for word in ['sell', 'should', 'when', 'best time', 'trend', 'recommendation', 'wait', 'now'])
    
    # Fetch prices if needed
    if needs_prices:
        try:
            from price_service import get_prices
            prices_data = get_prices(mentioned_crop)
            if prices_data and 'prices' in prices_data:
                context['prices'] = prices_data['prices'][:5]  # Top 5 prices
                context['count'] = prices_data.get('count', 0)
        except Exception as e:
            print(f"Error fetching prices: {e}")
    
    # Fetch insights if needed
    if needs_insights:
        try:
            from price_service import get_insights
            insights_data = get_insights(mentioned_crop)
            if insights_data and 'insights' in insights_data:
                context['insights'] = insights_data['insights']
        except Exception as e:
            print(f"Error fetching insights: {e}")
    
    return context

def generate_response(query, context_data, language='en'):
    """
    Generate response using Groq with AWS Bedrock fallback
    LLM decides what to do based on available data
    """
    # Build system prompt
    system_prompt = """You are FarmIntel, an agricultural intelligence assistant for Indian farmers.

Your expertise:
- Crop prices and market trends
- Selling recommendations
- Best mandi prices
- Agricultural advice

Rules:
- ONLY answer farming and agriculture questions
- If asked about non-farming topics, politely say: "I'm FarmIntel, specialized in agricultural intelligence. I can only help with farming, crop prices, and market insights. Please ask about agriculture."
- When you have price data: Format it clearly and give practical advice
- When you have insights data: Use the recommendation and trend to advise
- When you don't have data: Say "I don't have current data for that"
- Be specific with prices, mandis, and recommendations
- Keep answers concise and practical"""

    # Build user prompt with all available context
    user_prompt = f"User Query: {query}\n"
    
    # Add price data if available
    if context_data and 'prices' in context_data:
        crop = context_data.get('crop', 'crop')
        prices = context_data['prices']
        user_prompt += f"\n📊 CURRENT {crop.upper()} PRICES (Fresh Data):\n"
        user_prompt += "| Mandi | Price (₹/quintal) | State |\n"
        user_prompt += "|-------|------------------|-------|\n"
        for price in prices[:5]:
            mandi = price.get('mandi', 'Unknown')
            price_val = price.get('price', 0)
            state = price.get('state', 'N/A')
            user_prompt += f"| {mandi} | {price_val} | {state} |\n"
    
    # Add insights data if available
    if context_data and 'insights' in context_data:
        insights = context_data['insights']
        user_prompt += f"\n📈 MARKET INSIGHTS:\n"
        user_prompt += f"Recommendation: {insights.get('recommendation', 'N/A')}\n"
        user_prompt += f"Trend: {insights.get('trend', 'N/A')}\n"
        user_prompt += f"Best Price: ₹{insights.get('best_price', 0)} at {insights.get('best_mandi', 'N/A')}\n"
        if insights.get('avg_price'):
            user_prompt += f"Average Price: ₹{insights['avg_price']}\n"
    
    user_prompt += "\nProvide practical advice based on the data above:"
    
    # Try Groq first
    try:
        ai_response = call_groq(system_prompt, user_prompt)
        return ai_response, GROQ_MODEL
    except Exception as e:
        print(f"Groq API error: {e}")
        print("Falling back to Bedrock...")
        
        # Fallback to AWS Bedrock
        try:
            ai_response = call_bedrock(system_prompt, user_prompt)
            return ai_response, BEDROCK_MODEL
        except Exception as bedrock_error:
            print(f"Bedrock API error: {bedrock_error}")
            return "I'm having trouble processing your request right now. Please try again.", "fallback"

def call_bedrock(system_prompt, user_prompt):
    """
    Call AWS Bedrock API
    """
    # Check model type and use appropriate API format
    if 'nova' in BEDROCK_MODEL.lower():
        # Amazon Nova API format
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps({
                "messages": [{
                    "role": "user",
                    "content": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                }],
                "inferenceConfig": {
                    "max_new_tokens": 100,
                    "temperature": 0.7
                }
            })
        )
        
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text'].strip()
        
    elif 'llama' in BEDROCK_MODEL.lower():
        # Meta Llama API format
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps({
                "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "max_gen_len": 100,
                "temperature": 0.7,
                "top_p": 0.9
            })
        )
        
        result = json.loads(response['body'].read())
        return result['generation'].strip()
        
    else:
        # Claude API format (fallback)
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "system": system_prompt,
                "messages": [{
                    "role": "user",
                    "content": user_prompt
                }],
                "temperature": 0.7
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text'].strip()

def call_groq(system_prompt, user_prompt):
    """
    Call Groq API (fallback)
    """
    groq_api_key = get_groq_api_key()
    
    if not groq_api_key:
        raise Exception("Groq API key not configured")
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "top_p": 1
    }
    
    response = http.request(
        'POST',
        GROQ_API_URL,
        body=json.dumps(payload),
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        }
    )
    
    if response.status != 200:
        raise Exception(f"Groq API returned status {response.status}")
    
    result = json.loads(response.data.decode('utf-8'))
    return result['choices'][0]['message']['content'].strip()

def translate_response(text, target_language):
    """
    Translate response to target language using Bedrock
    """
    if target_language == 'en':
        return text
    
    language_map = {
        'hi': 'Hindi',
        'kn': 'Kannada',
        'ta': 'Tamil',
        'te': 'Telugu'
    }
    
    target_lang_name = language_map.get(target_language, 'Hindi')
    
    prompt = f"""Translate the following text to {target_lang_name}.
Keep the same tone and meaning.

Text: {text}

Translation:"""

    try:
        # Check model type and use appropriate API format
        if 'nova' in BEDROCK_MODEL.lower():
            # Amazon Nova API format
            response = bedrock.invoke_model(
                modelId=BEDROCK_MODEL,
                body=json.dumps({
                    "messages": [{
                        "role": "user",
                        "content": [{"text": prompt}]
                    }],
                    "inferenceConfig": {
                        "max_new_tokens": 500,
                        "temperature": 0.3
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            translated = result['output']['message']['content'][0]['text'].strip()
            
        elif 'llama' in BEDROCK_MODEL.lower():
            # Meta Llama API format
            response = bedrock.invoke_model(
                modelId=BEDROCK_MODEL,
                body=json.dumps({
                    "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                    "max_gen_len": 500,
                    "temperature": 0.3,
                    "top_p": 0.9
                })
            )
            
            result = json.loads(response['body'].read())
            translated = result['generation'].strip()
            
        else:
            # Claude API format (fallback)
            response = bedrock.invoke_model(
                modelId=BEDROCK_MODEL,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                })
            )
            
            result = json.loads(response['body'].read())
            translated = result['content'][0]['text'].strip()
        
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original if translation fails
