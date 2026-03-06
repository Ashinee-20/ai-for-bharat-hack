"""
LLM Service with LLM Decision Router
Groq primary + AWS Bedrock fallback
"""

import json
import os
import boto3
import urllib3

# AWS clients
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
ssm = boto3.client("ssm", region_name="ap-south-1")

# Models
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

http = urllib3.PoolManager()

_groq_api_key_cache = None


# -------------------------------
# API KEY FETCH
# -------------------------------
def get_groq_api_key():

    global _groq_api_key_cache

    if _groq_api_key_cache:
        return _groq_api_key_cache

    try:
        response = ssm.get_parameter(
            Name="/farmintel/groq-api-key",
            WithDecryption=True
        )
        _groq_api_key_cache = response["Parameter"]["Value"]
        return _groq_api_key_cache

    except Exception as e:
        print("SSM error:", e)
        return os.environ.get("GROQ_API_KEY", "")


# -------------------------------
# GROQ CALL
# -------------------------------
def call_groq(messages, max_tokens=150):

    groq_api_key = get_groq_api_key()

    if not groq_api_key:
        print("[ERROR] No Groq API key found")
        raise Exception("Groq API key not configured")

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens
    }

    print(f"[DEBUG] Calling Groq API with model: {GROQ_MODEL}")
    response = http.request(
        "POST",
        GROQ_API_URL,
        body=json.dumps(payload),
        headers={
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
    )

    print(f"[DEBUG] Groq response status: {response.status}")
    
    if response.status != 200:
        print(f"[ERROR] Groq API error {response.status}: {response.data.decode('utf-8')}")
        raise Exception(f"Groq error {response.status}")

    result = json.loads(response.data.decode("utf-8"))
    return result["choices"][0]["message"]["content"]


# -------------------------------
# BEDROCK FALLBACK
# -------------------------------
def call_bedrock(system_prompt, user_prompt):

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL,
        body=json.dumps({
            "messages": [{
                "role": "user",
                "content": [{"text": system_prompt + "\n\n" + user_prompt}]
            }],
            "inferenceConfig": {
                "max_new_tokens": 150,
                "temperature": 0.7
            }
        })
    )

    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"]


# -------------------------------
# ROUTER LLM
# -------------------------------
def llm_router(query, conversation_history=None):

    history_context = ""
    if conversation_history and len(conversation_history) > 0:
        history_context = "Previous conversation:\n"
        # Use last 5 messages for better context
        for msg in conversation_history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_context += f"{role}: {content}\n"
        history_context += "\n"

    router_prompt = f"""
You are a decision system for a farming AI.

Decide if APIs must be called based on the user query and conversation context.

Available APIs:

1. prices_api - for price information
2. insights_api - for market trends and selling recommendations

Supported crops:
wheat, rice, tomato, potato, onion, cotton, sugarcane

{history_context}Current User Query:
{query}

Return ONLY valid JSON (no markdown, no code blocks):

{{"crop": "wheat", "fetch_prices": true, "fetch_insights": false}}

Rules:
- If asking about price, cost, rate → fetch_prices
- If asking about selling, trends, recommendations, best time → fetch_insights
- If unrelated → both false
- Consider previous context when interpreting ambiguous queries
"""

    messages = [
        {"role": "system", "content": "Return ONLY valid JSON. No markdown. No code blocks."},
        {"role": "user", "content": router_prompt}
    ]

    try:
        print(f"[DEBUG] Calling Groq router for query: {query}")
        decision_text = call_groq(messages, 80)
        print(f"[DEBUG] Groq router response: {decision_text}")

        # Extract JSON from markdown code blocks if present
        if "```" in decision_text:
            print(f"[DEBUG] Extracting JSON from markdown code blocks")
            # Remove markdown code block markers
            decision_text = decision_text.replace("```json", "").replace("```", "").strip()
            print(f"[DEBUG] Cleaned response: {decision_text}")

        decision = json.loads(decision_text)
        print(f"[DEBUG] Parsed decision: {decision}")

        return decision

    except json.JSONDecodeError as je:
        print(f"[ERROR] Router JSON decode error: {je}")
        print(f"[ERROR] Raw response was: {decision_text}")
        return {
            "crop": None,
            "fetch_prices": False,
            "fetch_insights": False
        }
    except Exception as e:
        print(f"[ERROR] Router error: {e}")
        import traceback
        traceback.print_exc()

        return {
            "crop": None,
            "fetch_prices": False,
            "fetch_insights": False
        }


# -------------------------------
# CONTEXT FETCH
# -------------------------------
def build_context(query, conversation_history=None):

    decision = llm_router(query, conversation_history)

    crop = decision.get("crop")

    print(f"[ROUTER DECISION] Query: {query}, Crop: {crop}, Fetch Prices: {decision.get('fetch_prices')}, Fetch Insights: {decision.get('fetch_insights')}")

    if not crop:
        return {}

    context = {"crop": crop}

    try:
        print(f"[DEBUG] Attempting to import price_service functions...")
        from price_service import get_prices_data
        from price_service import get_insights_data
        print(f"[DEBUG] Successfully imported price_service functions")

        if decision.get("fetch_prices"):
            print(f"[API CALL] Fetching prices for {crop}")
            prices = get_prices_data(crop)

            if prices:
                print(f"[API RESULT] Got {len(prices)} price records for {crop}")
                # Convert Decimal to float for JSON serialization
                prices_converted = []
                for p in prices[:5]:
                    prices_converted.append({
                        'mandi': p['mandi'],
                        'state': p['state'],
                        'district': p['district'],
                        'price': float(p['price']),
                        'min_price': float(p['min_price']),
                        'max_price': float(p['max_price']),
                        'date': p['date'],
                        'variety': p['variety']
                    })
                context["prices"] = prices_converted
            else:
                print(f"[API RESULT] No prices returned for {crop}")

        if decision.get("fetch_insights"):
            print(f"[API CALL] Fetching insights for {crop}")
            insights = get_insights_data(crop)

            if insights:
                print(f"[API RESULT] Got insights for {crop}: {insights.get('recommendation')}")
                context["insights"] = insights
            else:
                print(f"[API RESULT] No insights returned for {crop}")

    except ImportError as ie:
        print(f"[ERROR] Import error: {ie}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"[ERROR] Context fetch error: {e}")
        import traceback
        traceback.print_exc()

    return context


# -------------------------------
# FINAL RESPONSE LLM
# -------------------------------
def generate_response(query, context, conversation_history=None):

    system_prompt = """
You are FarmIntel, an agricultural intelligence assistant.

Help farmers with:
- mandi prices (show as markdown table)
- selling recommendations
- crop market trends

Give short practical answers. Format prices as a markdown table when showing multiple prices.
"""

    user_prompt = f"User question: {query}\n\n"

    if "prices" in context:

        user_prompt += "Current Prices (format as markdown table):\n"
        user_prompt += "| Mandi | Price (₹) | State |\n"
        user_prompt += "|-------|-----------|-------|\n"

        for p in context["prices"]:
            user_prompt += f"| {p['mandi']} | {p['price']} | {p['state']} |\n"

    if "insights" in context:

        ins = context["insights"]

        user_prompt += "\nMarket Insight:\n"
        user_prompt += f"- Recommendation: {ins.get('recommendation')}\n"
        user_prompt += f"- Trend: {ins.get('trend')}\n"
        user_prompt += f"- Best Mandi: {ins.get('best_mandi')}\n"
        user_prompt += f"- Best Price: ₹{ins.get('best_price')}\n"

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add conversation history for context (last 5 messages)
    if conversation_history:
        for msg in conversation_history[-5:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

    messages.append({"role": "user", "content": user_prompt})

    try:

        return call_groq(messages)

    except Exception as e:

        print(f"[ERROR] Groq failure: {e}")

        return call_bedrock(system_prompt, user_prompt)


# -------------------------------
# LAMBDA HANDLER
# -------------------------------
def lambda_handler(event, context):

    if event.get("httpMethod") == "OPTIONS":

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": ""
        }

    body = json.loads(event.get("body", "{}"))

    query = body.get("query", "")
    conversation_history = body.get("conversation_history", [])

    if not query:

        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Query required"})
        }

    context_data = build_context(query, conversation_history)

    answer = generate_response(query, context_data, conversation_history)

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "POST,OPTIONS"
        },
        "body": json.dumps({
            "response": answer,
            "context": context_data
        })
    }