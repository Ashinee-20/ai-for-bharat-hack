# FarmIntel - AI For Bharat Hackathon

Agricultural intelligence platform for Indian farmers with real-time crop prices, market insights, and AI-powered recommendations.

## Quick Start

### Prerequisites
- AWS CLI configured (region: ap-south-1)
- SAM CLI installed
- Python 3.11+
- Node.js (for frontend)

### Deploy Backend
```bash
cd farmintel-v1
sam build
sam deploy
```

### Deploy Frontend
```bash
aws s3 sync frontend/ s3://farmintel-frontend-1938/ --cache-control "max-age=0"
aws cloudfront create-invalidation --distribution-id E3KAC8W81FR8AU --paths "/*"
```

## Architecture

**Frontend**: S3 + CloudFront (PWA)  
**Backend**: Lambda + API Gateway + DynamoDB  
**LLM**: Groq (primary) + AWS Bedrock (fallback)  
**Data**: Agmarknet API (prices)

## API Endpoints

Base URL: `https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod`

### Price API
```
GET /api/prices/{crop}
Response: { prices: [...], count: number }
```

### Insights API
```
GET /api/insights/{crop}
Response: { insights: { recommendation, trend, best_price, best_mandi, avg_price, price_range } }
```

### LLM API
```
POST /api/llm/query
Body: { query: string, language: "en", context?: object }
Response: { response: string, model: string }
```

## Configuration

### Environment Variables
- `BEDROCK_MODEL_ID`: us.amazon.nova-lite-v1:0
- `DYNAMODB_TABLE`: farmintel-prices

### AWS Resources
- **Lambda Functions**: IVRHandlerFunction, PriceServiceFunction, LLMServiceFunction
- **DynamoDB Table**: farmintel-prices (24-hour TTL)
- **S3 Bucket**: farmintel-frontend-1938
- **CloudFront Distribution**: E3KAC8W81FR8AU
- **Parameter Store**: /farmintel/groq-api-key (SecureString)

## Features

- ✅ Real-time crop prices (7 crops)
- ✅ Market trend analysis
- ✅ AI-powered recommendations
- ✅ Smart query routing (LLM decides what data to fetch)
- ✅ Price + Insights context in LLM responses
- ✅ PWA with offline support
- ✅ CORS enabled
- ✅ 24-hour price caching

## Supported Crops

wheat, rice, tomato, potato, onion, cotton, sugarcane

## Testing & Debugging

### Send Test Request (PowerShell)

**Simple Query:**
```powershell
$body = @{
    query = "What is the price of wheat?"
    conversation_history = @()
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod/api/llm/query" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

**With Conversation Context:**
```powershell
$body = @{
    query = "Should I sell it now?"
    conversation_history = @(
        @{role = "user"; content = "What is the price of rice?"},
        @{role = "assistant"; content = "The current price of rice is around 2500 per quintal."}
    )
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod/api/llm/query" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

### Check CloudWatch Logs

**Get Latest Log Stream:**
```powershell
$logGroup = "/aws/lambda/farmintel-v1-LLMServiceFunction-sQsS4HJSzTdZ"
$streams = aws logs describe-log-streams --log-group-name $logGroup --region ap-south-1 --order-by LastEventTime --descending --query 'logStreams[0].logStreamName' --output text
Write-Host "Latest stream: $streams"
```

**View All Logs:**
```powershell
aws logs get-log-events --log-group-name $logGroup --log-stream-name $streams --region ap-south-1 --query 'events[*].message' --output text
```

**Filter for API Calls:**
```powershell
aws logs get-log-events --log-group-name $logGroup --log-stream-name $streams --region ap-south-1 --query 'events[*].message' --output text | Select-String "\[API\]|\[ROUTER\]|\[ERROR\]"
```

**Real-time Log Tail:**
```bash
aws logs tail /aws/lambda/farmintel-v1-LLMServiceFunction-sQsS4HJSzTdZ --region ap-south-1 --follow
```

### Verify API Calls Are Working

**Check Router Decision:**
```powershell
# Look for this in logs:
# [ROUTER DECISION] Query: What is the price of wheat?, Crop: wheat, Fetch Prices: True, Fetch Insights: False
```

**Check Price Fetch:**
```powershell
# Look for this in logs:
# [API CALL] Fetching prices for wheat
# [API RESULT] Got 10 price records for wheat
```

**Check for Errors:**
```powershell
# Look for this in logs:
# [ERROR] - indicates something went wrong
```

### Test All Supported Crops

```powershell
$crops = @("wheat", "rice", "tomato", "potato", "onion", "cotton", "sugarcane")

foreach ($crop in $crops) {
    $body = @{
        query = "What is the price of $crop`?"
        conversation_history = @()
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "https://aj59v1wf4j.execute-api.ap-south-1.amazonaws.com/Prod/api/llm/query" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $body

    $data = $response.Content | ConvertFrom-Json
    Write-Host "$crop - Response length: $($data.response.Length) chars"
}
```

### Monitoring

```bash
# Lambda logs
aws logs tail /aws/lambda/farmintel-v1-LLMServiceFunction-sQsS4HJSzTdZ --follow

# Check Groq API key
aws ssm get-parameter --name /farmintel/groq-api-key --with-decryption

# CloudFront status
aws cloudfront get-distribution --id E3KAC8W81FR8AU --query 'Distribution.Status'

# DynamoDB cache stats
aws dynamodb scan --table-name farmintel-prices --region ap-south-1 --select COUNT
```

## Cost

**Current**: $0/month (within AWS free tier)  
**Limits**: 1M Lambda requests/month, 25GB DynamoDB, 1TB CloudFront

## Live URL

https://d1ktbyzym5umyt.cloudfront.net

## Project Structure

```
farmintel-v1/
├── lambda/
│   ├── llm_service.py (LLM + auto-fetch prices/insights)
│   ├── price_service.py (Agmarknet API + DynamoDB cache)
│   └── ivr_handler.py
├── template.yaml (SAM template)
└── samconfig.toml

frontend/
├── index.html
├── app.js (Smart query routing to LLM)
├── styles.css
├── sw.js (Service worker)
└── manifest.json
```

## How It Works

1. User asks question → Frontend sends to LLM API
2. Frontend includes last 5 messages as conversation context
3. LLM analyzes query and conversation history, then decides:
   - Need prices? → Fetches from Agmarknet
   - Need insights? → Calculates from prices
   - Just answer? → Responds with farming advice
4. LLM gets context data and generates response with markdown tables
5. Response sent back to frontend with context metadata

### Conversation Context

The system maintains conversation history to understand follow-up questions:

**Example Flow:**
```
User: "What is the price of rice?"
LLM: "The current price of rice is ₹2500 per quintal..."

User: "Should I sell it now?"
LLM: (understands this is about rice from context)
     "Yes, I recommend selling now because..."

User: "What about Karnataka?"
LLM: (understands this is about rice prices in Karnataka)
     "In Karnataka, the price is ₹2450 per quintal..."
```

**How It Works:**
- Frontend stores last 20 messages in localStorage
- When sending query, frontend sends last 5 messages as context
- Backend uses these 5 messages to inform router decision
- Backend includes these 5 messages in LLM response generation
- This keeps context window small while maintaining conversation flow

## Troubleshooting

### API Returns Empty Response
**Check logs for:**
```
[ERROR] Router error: ...
[ERROR] Context fetch error: ...
```
**Solution:** Check Groq API key in Parameter Store
```bash
aws ssm get-parameter --name /farmintel/groq-api-key --with-decryption --region ap-south-1
```

### Prices Not Showing in Response
**Check logs for:**
```
[API CALL] Fetching prices for wheat
[API RESULT] Got 0 price records for wheat
```
**Solution:** Agmarknet API might be down. Check mock data is returned:
```bash
# Look for this in logs:
# Agmarknet API error: ... (returns mock data for development)
```

### DynamoDB Cache Errors
**Check logs for:**
```
Cache read error: AccessDeniedException
Cache write error: Float types are not supported
```
**Solution:** 
- Ensure LLMServiceFunction has DynamoDBCrudPolicy
- Prices are converted to Decimal before saving

### Conversation Context Not Working
**Check logs for:**
```
[DEBUG] Parsed decision: {'crop': 'rice', 'fetch_prices': True, ...}
```
**Solution:** Ensure frontend is sending conversation_history array:
```powershell
# Verify in request body:
"conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
]
```

### JSON Parsing Errors
**Check logs for:**
```
[ERROR] Router JSON decode error: Expecting value: line 1 column 1
```
**Solution:** Groq might be returning markdown code blocks. This is now handled automatically by extracting JSON from ```json ... ``` blocks.

### High Latency
**Typical response time:** 1.5-2 seconds
- Router decision: ~500ms
- Price fetch: ~300ms  
- Response generation: ~700ms

**If slower:**
- Check Groq API status
- Check DynamoDB throttling
- Check Lambda cold start (first request slower)
