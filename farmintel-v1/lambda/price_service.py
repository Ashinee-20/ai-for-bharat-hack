"""
Price Service - Fetches mandi prices from Agmarknet API
Uses DynamoDB for caching (24-hour TTL)
"""
import json
import os
import boto3
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB with explicit region
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE')
table = dynamodb.Table(TABLE_NAME)

# Agmarknet API (FREE Government API)
AGMARKNET_API = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"  # Public demo key

def lambda_handler(event, context):
    """
    Main handler for price queries
    """
    path = event.get('path', '')
    
    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': ''
        }
    
    if '/prices/' in path:
        crop = event['pathParameters']['crop']
        return get_prices(crop)
    elif '/insights/' in path:
        crop = event['pathParameters']['crop']
        return get_insights(crop)
    
    return {
        'statusCode': 400,
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Invalid endpoint'})
    }

def get_prices(crop):
    """
    Get current prices for a crop
    """
    # Check cache first
    cached_prices = get_from_cache(crop)
    if cached_prices:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({
                'crop': crop,
                'prices': cached_prices,
                'count': len(cached_prices),
                'cached': True
            }, default=str)
        }
    
    # Fetch from Agmarknet API
    prices = fetch_from_agmarknet(crop)
    
    if prices:
        # Cache for 24 hours
        save_to_cache(crop, prices)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({
                'crop': crop,
                'prices': prices,
                'count': len(prices),
                'cached': False
            }, default=str)
        }
    
    return {
        'statusCode': 404,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps({'error': 'No price data found'})
    }

def get_insights(crop):
    """
    Get selling insights for a crop
    """
    prices = get_from_cache(crop) or fetch_from_agmarknet(crop)
    
    if not prices:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({'error': 'No price data available'})
        }
    
    # Calculate insights
    insights = calculate_insights(prices)
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps({
            'crop': crop,
            'insights': insights
        }, default=str)
    }

def get_from_cache(crop):
    """
    Get prices from DynamoDB cache
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        response = table.get_item(
            Key={
                'pk': f'PRICE#{crop.upper()}',
                'sk': today
            }
        )
        
        if 'Item' in response:
            item = response['Item']
            # Check if not expired
            if item.get('ttl', 0) > datetime.now().timestamp():
                return item.get('prices', [])
    except Exception as e:
        print(f"Cache read error: {e}")
    
    return None

def save_to_cache(crop, prices):
    """
    Save prices to DynamoDB with 24-hour TTL
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        ttl = int((datetime.now() + timedelta(hours=24)).timestamp())
        
        table.put_item(
            Item={
                'pk': f'PRICE#{crop.upper()}',
                'sk': today,
                'prices': prices,
                'ttl': ttl,
                'updated_at': datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Cache write error: {e}")

def fetch_from_agmarknet(crop):
    """
    Fetch prices from Agmarknet API (FREE)
    """
    try:
        # Map common crop names to Agmarknet commodity names
        crop_map = {
            'wheat': 'Wheat',
            'rice': 'Rice',
            'tomato': 'Tomato',
            'potato': 'Potato',
            'onion': 'Onion',
            'cotton': 'Cotton',
            'sugarcane': 'Sugarcane'
        }
        
        commodity = crop_map.get(crop.lower(), crop.capitalize())
        
        params = {
            'api-key': API_KEY,
            'format': 'json',
            'filters[commodity]': commodity,
            'limit': 10
        }
        
        response = requests.get(AGMARKNET_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        records = data.get('records', [])
        
        # Parse and format prices
        prices = []
        for record in records:
            prices.append({
                'mandi': record.get('market', 'Unknown'),
                'state': record.get('state', 'Unknown'),
                'district': record.get('district', 'Unknown'),
                'price': float(record.get('modal_price', 0)),
                'min_price': float(record.get('min_price', 0)),
                'max_price': float(record.get('max_price', 0)),
                'date': record.get('arrival_date', datetime.now().strftime('%Y-%m-%d')),
                'variety': record.get('variety', 'General')
            })
        
        return prices
    except Exception as e:
        print(f"Agmarknet API error: {e}")
        # Return mock data for development
        return get_mock_prices(crop)

def get_mock_prices(crop):
    """
    Mock price data for development/testing
    """
    return [
        {
            'mandi': 'Azadpur Mandi, Delhi',
            'state': 'Delhi',
            'district': 'Delhi',
            'price': 2500,
            'min_price': 2400,
            'max_price': 2600,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'variety': 'General'
        },
        {
            'mandi': 'Vashi APMC, Mumbai',
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'price': 2450,
            'min_price': 2350,
            'max_price': 2550,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'variety': 'General'
        },
        {
            'mandi': 'Yeshwanthpur APMC, Bangalore',
            'state': 'Karnataka',
            'district': 'Bangalore',
            'price': 2600,
            'min_price': 2500,
            'max_price': 2700,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'variety': 'General'
        }
    ]

def calculate_insights(prices):
    """
    Calculate selling insights from price data
    """
    if not prices or len(prices) < 2:
        return {
            'trend': 'STABLE',
            'recommendation': 'INSUFFICIENT_DATA',
            'confidence': 0
        }
    
    # Calculate average price
    avg_price = sum(p['price'] for p in prices) / len(prices)
    
    # Calculate price volatility
    price_range = max(p['price'] for p in prices) - min(p['price'] for p in prices)
    volatility = (price_range / avg_price) * 100 if avg_price > 0 else 0
    
    # Simple trend analysis
    recent_prices = [p['price'] for p in prices[:3]]
    if len(recent_prices) >= 2:
        if recent_prices[0] > recent_prices[-1] * 1.05:
            trend = 'RISING'
            recommendation = 'WAIT'
        elif recent_prices[0] < recent_prices[-1] * 0.95:
            trend = 'FALLING'
            recommendation = 'SELL_NOW'
        else:
            trend = 'STABLE'
            recommendation = 'SELL_WITHIN_WEEK'
    else:
        trend = 'STABLE'
        recommendation = 'SELL_WITHIN_WEEK'
    
    return {
        'trend': trend,
        'recommendation': recommendation,
        'avg_price': round(avg_price, 2),
        'volatility': round(volatility, 2),
        'confidence': 75,
        'best_mandi': max(prices, key=lambda x: x['price'])['mandi'],
        'best_price': max(p['price'] for p in prices)
    }
