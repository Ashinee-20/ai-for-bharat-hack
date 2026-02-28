"""
AWS Connect IVR Handler
Handles incoming calls and routes to appropriate services
"""
import json
import os
import boto3
from datetime import datetime

# AWS Clients - Initialize with explicit region
bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
polly = boto3.client('polly', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

# Configuration
TABLE_NAME = os.environ.get('DYNAMODB_TABLE')
BEDROCK_MODEL = os.environ.get('BEDROCK_MODEL_ID')

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Main handler for AWS Connect contact flow
    """
    print(f"Event: {json.dumps(event)}")
    
    # Parse input from AWS Connect
    contact_data = event.get('Details', {}).get('ContactData', {})
    parameters = event.get('Details', {}).get('Parameters', {})
    
    # Get user input (from DTMF or speech)
    user_input = parameters.get('userInput', '')
    language = parameters.get('language', 'en-IN')
    session_id = contact_data.get('ContactId', '')
    
    # Route based on intent
    intent = classify_intent(user_input, language)
    
    if intent == 'PRICE_QUERY':
        response = handle_price_query(user_input, language)
    elif intent == 'SELLING_INSIGHT':
        response = handle_selling_insight(user_input, language)
    else:
        response = handle_general_query(user_input, language)
    
    # Convert response to speech
    speech_url = text_to_speech(response, language)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'response': response,
            'speechUrl': speech_url,
            'intent': intent,
            'sessionId': session_id
        })
    }

def classify_intent(user_input, language):
    """
    Classify user intent using AWS Bedrock
    """
    prompt = f"""Classify the following farmer query into one of these intents:
- PRICE_QUERY: Asking about crop prices
- SELLING_INSIGHT: Asking when to sell or market trends
- GENERAL: Other questions

Query: {user_input}
Language: {language}

Respond with only the intent name."""

    try:
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            })
        )
        
        result = json.loads(response['body'].read())
        intent = result['content'][0]['text'].strip()
        return intent if intent in ['PRICE_QUERY', 'SELLING_INSIGHT'] else 'GENERAL'
    except Exception as e:
        print(f"Error classifying intent: {e}")
        return 'GENERAL'

def handle_price_query(user_input, language):
    """
    Handle price-related queries
    """
    # Extract crop name from input
    crop = extract_crop_name(user_input)
    
    # Get prices from cache or API
    prices = get_crop_prices(crop)
    
    if not prices:
        return get_response_in_language(
            "Sorry, I couldn't find price information for that crop.",
            language
        )
    
    # Format response
    response = format_price_response(prices, language)
    return response

def handle_selling_insight(user_input, language):
    """
    Handle selling insight queries using LLM
    """
    crop = extract_crop_name(user_input)
    prices = get_crop_prices(crop)
    
    if not prices:
        return get_response_in_language(
            "I need price data to provide selling insights.",
            language
        )
    
    # Generate insights using Bedrock
    prompt = f"""You are an agricultural advisor helping Indian farmers.
Based on the following price data, provide selling-time insights:

Crop: {crop}
Recent Prices: {json.dumps(prices[:5])}

Provide:
1. Current market trend (rising/falling/stable)
2. Recommendation (sell now / wait / sell within week)
3. Brief reasoning

Keep response under 100 words, conversational tone."""

    try:
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            })
        )
        
        result = json.loads(response['body'].read())
        insight = result['content'][0]['text'].strip()
        return get_response_in_language(insight, language)
    except Exception as e:
        print(f"Error generating insight: {e}")
        return "Unable to generate insights at this time."

def handle_general_query(user_input, language):
    """
    Handle general queries
    """
    return get_response_in_language(
        "I can help you with crop prices and selling insights. What would you like to know?",
        language
    )

def get_crop_prices(crop):
    """
    Get crop prices from DynamoDB cache or Agmarknet API
    """
    # Check cache first
    try:
        response = table.get_item(
            Key={
                'pk': f'PRICE#{crop.upper()}',
                'sk': datetime.now().strftime('%Y-%m-%d')
            }
        )
        
        if 'Item' in response:
            return response['Item'].get('prices', [])
    except Exception as e:
        print(f"Error reading from cache: {e}")
    
    # Fetch from API (implement Agmarknet integration)
    # For now, return mock data
    return [
        {'mandi': 'Delhi', 'price': 2500, 'date': '2026-02-28'},
        {'mandi': 'Mumbai', 'price': 2450, 'date': '2026-02-28'},
        {'mandi': 'Bangalore', 'price': 2600, 'date': '2026-02-28'}
    ]

def extract_crop_name(text):
    """
    Extract crop name from user input
    Simple keyword matching for V1
    """
    crops = ['wheat', 'rice', 'tomato', 'potato', 'onion', 'cotton', 'sugarcane']
    text_lower = text.lower()
    
    for crop in crops:
        if crop in text_lower:
            return crop
    
    return 'wheat'  # default

def format_price_response(prices, language):
    """
    Format price data into conversational response
    """
    if not prices:
        return "No price data available."
    
    response = "Here are the current prices:\n"
    for p in prices[:3]:  # Top 3 mandis
        response += f"{p['mandi']}: ₹{p['price']} per quintal\n"
    
    return get_response_in_language(response, language)

def get_response_in_language(text, language):
    """
    Translate response to target language
    For V1, supporting English, Hindi, Kannada
    """
    # TODO: Implement translation using Bedrock or AWS Translate
    # For now, return English
    return text

def text_to_speech(text, language):
    """
    Convert text to speech using AWS Polly
    """
    try:
        # Map language codes to Polly voice IDs
        voice_map = {
            'en-IN': 'Aditi',
            'hi-IN': 'Aditi',
            'kn-IN': 'Aditi'  # Polly supports limited Indian languages
        }
        
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_map.get(language, 'Aditi'),
            Engine='neural'
        )
        
        # In production, save to S3 and return URL
        # For now, return placeholder
        return "https://placeholder-audio-url.mp3"
    except Exception as e:
        print(f"Error in TTS: {e}")
        return None
