# AgriBridge AI Platform

An offline-first agricultural intelligence platform that enables farmers to access market prices, crop advisory, and buyer connections through voice (IVR), SMS, and mobile applications.

## Architecture

- **Backend**: Python with AWS Lambda (serverless)
- **Databases**: DynamoDB (NoSQL), PostgreSQL (relational), OpenSearch (vector search)
- **AI/ML**: AWS Bedrock for LLM, RAG for knowledge-grounded responses
- **Mobile**: React Native with quantized on-device models
- **Infrastructure**: AWS CDK for infrastructure-as-code

## Project Structure

```
agribridge-ai/
├── src/
│   ├── services/          # Lambda function handlers
│   ├── models/            # Pydantic data models
│   ├── utils/             # Shared utilities
│   └── config/            # Configuration management
├── infrastructure/        # AWS CDK infrastructure code
├── tests/                 # Unit and property-based tests
├── scripts/               # Utility scripts
└── docs/                  # Additional documentation
```

## Setup

### Prerequisites

- Python 3.11+
- AWS CLI configured
- Docker (for LocalStack)
- Node.js 18+ (for AWS CDK)

### Local Development

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Start LocalStack for local AWS emulation:
```bash
docker-compose up -d
```

4. Run tests:
```bash
pytest tests/
```

### Infrastructure Deployment

1. Install AWS CDK:
```bash
npm install -g aws-cdk
```

2. Deploy infrastructure:
```bash
cd infrastructure
cdk deploy
```

## Testing

The project uses both unit tests and property-based tests:

- **Unit Tests**: Specific examples and edge cases
- **Property Tests**: Universal properties across all inputs (using Hypothesis)

Run all tests:
```bash
pytest tests/ -v
```

Run only property tests:
```bash
pytest tests/ -v -m property
```

## Environment Variables

Create a `.env` file with:

```
AWS_REGION=ap-south-1
DYNAMODB_TABLE_PREFIX=agribridge
RDS_HOST=localhost
RDS_DATABASE=agribridge
RDS_USER=postgres
RDS_PASSWORD=password
OPENSEARCH_ENDPOINT=localhost:9200
BEDROCK_MODEL_ID=anthropic.claude-v2
```

## License

Proprietary - Team CodeAshRam
