# Development Guide

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- AWS CLI (optional, for deployment)
- Node.js 18+ (for AWS CDK)

### Initial Setup

1. Clone the repository
2. Run the setup script:
   ```bash
   make setup
   ```
   Or manually:
   ```bash
   bash scripts/setup_local.sh
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Start local services:
   ```bash
   make docker-up
   ```

## Project Structure

```
agribridge-ai/
├── src/                    # Source code
│   ├── models/            # Pydantic data models
│   ├── services/          # Lambda function handlers
│   ├── utils/             # Shared utilities
│   └── config/            # Configuration
├── infrastructure/        # AWS CDK infrastructure code
├── tests/                 # Test suite
│   ├── test_models/      # Model tests
│   ├── test_services/    # Service tests
│   └── test_utils/       # Utility tests
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

## Development Workflow

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Property-based tests only
make test-property

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type checking
mypy src/
```

### Local Services

The project uses LocalStack for local AWS service emulation:

- **DynamoDB**: http://localhost:4566
- **S3**: http://localhost:4566
- **SNS**: http://localhost:4566
- **PostgreSQL**: localhost:5432
- **OpenSearch**: http://localhost:9200

Access services using AWS CLI with LocalStack:
```bash
aws --endpoint-url=http://localhost:4566 dynamodb list-tables
```

## Testing Strategy

### Unit Tests

Unit tests focus on specific functionality with concrete examples:

```python
@pytest.mark.unit
def test_price_data_validation():
    """Test that price data validates correctly."""
    price = PriceData(
        mandi_name="Delhi Mandi",
        mandi_location=GeoLocation(latitude=28.6, longitude=77.2),
        crop_name="wheat",
        price_per_quintal=2000.0,
        source="test",
    )
    assert price.price_per_quintal == 2000.0
```

### Property-Based Tests

Property tests verify universal properties across many inputs:

```python
from hypothesis import given, strategies as st

@pytest.mark.property
@given(
    latitude=st.floats(min_value=-90, max_value=90),
    longitude=st.floats(min_value=-180, max_value=180),
)
def test_geolocation_roundtrip(latitude, longitude):
    """Property: Any valid coordinates should create valid GeoLocation."""
    location = GeoLocation(latitude=latitude, longitude=longitude)
    assert location.latitude == latitude
    assert location.longitude == longitude
```

## Infrastructure Deployment

### Using AWS CDK

1. Install CDK dependencies:
   ```bash
   cd infrastructure
   pip install -r requirements.txt
   ```

2. Bootstrap CDK (first time only):
   ```bash
   cdk bootstrap
   ```

3. Deploy:
   ```bash
   make deploy
   # Or: cd infrastructure && cdk deploy
   ```

4. View changes before deploying:
   ```bash
   cd infrastructure && cdk diff
   ```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `AWS_REGION`: AWS region (default: ap-south-1)
- `ENVIRONMENT`: development/staging/production
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR
- `JWT_SECRET_KEY`: Secret key for JWT tokens (change in production!)

## Common Tasks

### Adding a New Service

1. Create service file in `src/services/`
2. Define interface and implementation
3. Add Lambda handler function
4. Create unit tests in `tests/test_services/`
5. Add CDK Lambda function in infrastructure

### Adding a New Model

1. Create model in `src/models/`
2. Add to `__init__.py` exports
3. Create validation tests
4. Document fields with descriptions

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
```

View LocalStack logs:
```bash
docker-compose logs -f localstack
```

## Troubleshooting

### LocalStack not starting

```bash
docker-compose down
docker-compose up -d
```

### Database connection errors

Ensure PostgreSQL is running:
```bash
docker-compose ps
```

### Import errors

Reinstall dependencies:
```bash
pip install -r requirements-dev.txt
```

## Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [LocalStack Documentation](https://docs.localstack.cloud/)
