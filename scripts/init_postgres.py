#!/usr/bin/env python3
"""Script to initialize PostgreSQL database with schema."""

import psycopg2
from src.utils.config import get_config

config = get_config()

# SQL schema from design document
SCHEMA_SQL = """
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Buyers Table
CREATE TABLE IF NOT EXISTS buyers (
    buyer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    location GEOGRAPHY(POINT, 4326),
    district VARCHAR(100),
    state VARCHAR(100),
    crop_interests TEXT[],
    typical_volume_quintal INTEGER,
    max_purchase_distance_km INTEGER,
    quality_preferences TEXT[],
    rating DECIMAL(3,2),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_buyers_location ON buyers USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_buyers_district ON buyers(district);

-- Crop Availability Table
CREATE TABLE IF NOT EXISTS crop_availability (
    availability_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id VARCHAR(100) NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    variety VARCHAR(100),
    quantity_quintal DECIMAL(10,2) NOT NULL,
    quality_grade VARCHAR(10),
    harvest_date DATE,
    location GEOGRAPHY(POINT, 4326),
    district VARCHAR(100),
    price_expectation DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'AVAILABLE',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crop_location ON crop_availability USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_crop_type ON crop_availability(crop_type);
CREATE INDEX IF NOT EXISTS idx_crop_status ON crop_availability(status);

-- Matches Table
CREATE TABLE IF NOT EXISTS matches (
    match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id VARCHAR(100) NOT NULL,
    buyer_id UUID NOT NULL,
    availability_id UUID NOT NULL,
    match_score DECIMAL(5,2),
    distance_km DECIMAL(10,2),
    farmer_consent BOOLEAN DEFAULT FALSE,
    buyer_viewed BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id),
    FOREIGN KEY (availability_id) REFERENCES crop_availability(availability_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_farmer ON matches(farmer_id);
CREATE INDEX IF NOT EXISTS idx_matches_buyer ON matches(buyer_id);

-- Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL,
    farmer_id VARCHAR(100) NOT NULL,
    buyer_id UUID NOT NULL,
    crop_type VARCHAR(100),
    quantity_quintal DECIMAL(10,2),
    price_per_quintal DECIMAL(10,2),
    total_amount DECIMAL(12,2),
    transaction_date DATE,
    status VARCHAR(20) DEFAULT 'COMPLETED',
    farmer_rating INTEGER CHECK (farmer_rating BETWEEN 1 AND 5),
    buyer_rating INTEGER CHECK (buyer_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id)
);
"""

try:
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host=config.rds_host,
        port=config.rds_port,
        database=config.rds_database,
        user=config.rds_user,
        password=config.rds_password,
    )
    
    cursor = conn.cursor()
    
    print("Creating schema...")
    cursor.execute(SCHEMA_SQL)
    conn.commit()
    
    print("✓ PostgreSQL schema initialized successfully!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error initializing PostgreSQL: {e}")
    raise
