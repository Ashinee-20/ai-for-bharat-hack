"""
LLM Service - AWS Bedrock Integration
Uses Claude Haiku (cheapest model) for conversational AI
"""
import json
import os
import boto3

# Initialize boto3 client without explicit region (uses Lambda's default region)
bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
BEDROCK_MODEL = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')

def lambda_handler(event, context):
    """
    Main handler for LLM queries
    """
    body = json.loads(event.get('body', '{}'))
    
    query = body.get('query', '')
    context_data = body.get('context', {})
    language = body.get('language', 'en')
    
    if not query:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Query is required'})
        }
    
    response = generate_response(query, context_data, language)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'response': response,
            'model': BEDROCK_MODEL
        })
    }

def generate_response(query, context_data, language='en'):
    """
    Generate response using AWS Bedrock Claude Haiku
    """
    # Build system prompt
    system_prompt = """You are an AI assistant helping Indian farmers with agricultural information.
You provide:
- Crop price information
- Selling-time recommendations
- Market trend insights

Keep responses:
- Concise (under 150 words)
- Conversational and friendly
- Practical and actionable
- In simple language farmers can understand"""

    # Build user prompt with context
    user_prompt = f"Farmer Query: {query}\n\n"
    
    if context_data:
        user_prompt += "Context:\n"
        if 'prices' in context_data:
            user_prompt += f"Price Data: {json.dumps(context_data['prices'][:3])}\n"
        if 'insights' in context_data:
            user_prompt += f"Market Insights: {json.dumps(context_data['insights'])}\n"
    
    user_prompt += f"\nLanguage: {language}\nProvide a helpful response."
    
    try:
        # Call Bedrock API
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 400,
                "system": system_prompt,
                "messages": [{
                    "role": "user",
                    "content": user_prompt
                }],
                "temperature": 0.7
            })
        )
        
        result = json.loads(response['body'].read())
        ai_response = result['content'][0]['text'].strip()
        
        return ai_response
    except Exception as e:
        print(f"Bedrock API error: {e}")
        return "I'm having trouble processing your request right now. Please try again."

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
