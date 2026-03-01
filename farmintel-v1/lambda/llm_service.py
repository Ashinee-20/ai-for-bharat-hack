"""
LLM Service - AWS Bedrock Integration
Uses Amazon Nova Lite (free model) for conversational AI
"""
import json
import os
import boto3

# Initialize boto3 client for Bedrock in us-east-1 (more models available)
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
BEDROCK_MODEL = os.environ.get('BEDROCK_MODEL_ID', 'us.amazon.nova-lite-v1:0')

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
    Generate response using AWS Bedrock (supports Nova, Claude, Llama)
    """
    # Build concise system prompt
    system_prompt = """You are a farming advisor. Give brief, practical advice about crop prices and selling."""

    # Build minimal user prompt
    user_prompt = f"Query: {query}\n"
    
    if context_data and 'prices' in context_data:
        prices = context_data['prices'][:2]  # Only use top 2 prices
        user_prompt += f"Prices: {prices}\n"
    
    user_prompt += "Answer in under 50 words."
    
    try:
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
            ai_response = result['output']['message']['content'][0]['text'].strip()
            
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
            ai_response = result['generation'].strip()
            
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
