#!/usr/bin/env python3
"""Script to create DynamoDB tables in LocalStack."""

import boto3
from src.utils.config import get_config

config = get_config()

# Create DynamoDB client
dynamodb = boto3.client(
    "dynamodb",
    region_name=config.aws_region,
    endpoint_url=config.dynamodb_endpoint_url,
)

tables = [
    {
        "TableName": f"{config.dynamodb_table_prefix}-farmers",
        "KeySchema": [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": f"{config.dynamodb_table_prefix}-price-cache",
        "KeySchema": [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": f"{config.dynamodb_table_prefix}-query-logs",
        "KeySchema": [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": f"{config.dynamodb_table_prefix}-conversations",
        "KeySchema": [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": f"{config.dynamodb_table_prefix}-otp",
        "KeySchema": [
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
]

for table_config in tables:
    try:
        print(f"Creating table: {table_config['TableName']}")
        dynamodb.create_table(**table_config)
        print(f"✓ Created {table_config['TableName']}")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠ Table {table_config['TableName']} already exists")
    except Exception as e:
        print(f"✗ Error creating {table_config['TableName']}: {e}")

print("\nDynamoDB tables setup complete!")
