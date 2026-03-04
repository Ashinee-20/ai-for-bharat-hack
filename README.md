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

## Monitoring

```bash
# Lambda logs
aws logs tail /aws/lambda/farmintel-v1-LLMServiceFunction-sQsS4HJSzTdZ --follow

# Check Groq API key
aws ssm get-parameter --name /farmintel/groq-api-key --with-decryption

# CloudFront status
aws cloudfront get-distribution --id E3KAC8W81FR8AU --query 'Distribution.Status'
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
2. LLM analyzes query and decides:
   - Need prices? → Fetches from Agmarknet
   - Need insights? → Calculates from prices
   - Just answer? → Responds with farming advice
3. LLM gets context data and generates response
4. Response sent back to frontend

## Notes

- Questions are NOT stored (can enable later)
- Prices cached for 24 hours in DynamoDB
- LLM refuses non-farming questions
- Service Worker handles offline PWA functionality
