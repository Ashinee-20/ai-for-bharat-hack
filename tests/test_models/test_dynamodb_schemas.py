"""Unit tests for DynamoDB schema models."""

import pytest
from datetime import datetime, timedelta
from src.models.dynamodb_schemas import (
    FarmerRecord,
    BuyerRecord,
    PriceCacheRecord,
    QueryLogRecord,
    ConversationRecord,
    DYNAMODB_TABLES,
)
from src.models.common import GeoLocation, Language


class TestFarmerRecord:
    """Test cases for FarmerRecord."""

    def test_create_keys(self):
        """Test key creation for farmer record."""
        phone_hash = "abc123"
        user_id = "farmer_001"
        district = "Delhi"
        
        keys = FarmerRecord.create_keys(phone_hash, user_id, district)
        
        assert keys["PK"] == "FARMER#abc123"
        assert keys["SK"] == "PROFILE"
        assert keys["GSI1PK"] == "DISTRICT#Delhi"
        assert keys["GSI1SK"] == "FARMER#farmer_001"

    def test_farmer_record_creation(self):
        """Test creating a complete farmer record."""
        location = GeoLocation(latitude=28.6139, longitude=77.2090)
        keys = FarmerRecord.create_keys("hash123", "farmer_001", "Delhi")
        
        record = FarmerRecord(
            **keys,
            user_id="farmer_001",
            phone_number="encrypted_phone",
            phone_hash="hash123",
            name="Test Farmer",
            language=Language.HINDI,
            location=location,
            district="Delhi",
            land_size=5.0,
            crop_types=["wheat", "rice"],
            soil_type="loamy",
        )
        
        assert record.PK == "FARMER#hash123"
        assert record.SK == "PROFILE"
        assert record.user_id == "farmer_001"
        assert record.name == "Test Farmer"
        assert record.land_size == 5.0
        assert len(record.crop_types) == 2
        assert record.rating is None

    def test_farmer_record_with_rating(self):
        """Test farmer record with rating."""
        location = GeoLocation(latitude=28.6139, longitude=77.2090)
        keys = FarmerRecord.create_keys("hash123", "farmer_001", "Delhi")
        
        record = FarmerRecord(
            **keys,
            user_id="farmer_001",
            phone_number="encrypted_phone",
            phone_hash="hash123",
            name="Test Farmer",
            location=location,
            district="Delhi",
            land_size=5.0,
            crop_types=["wheat"],
            soil_type="loamy",
            rating=4.5,
        )
        
        assert record.rating == 4.5

    def test_farmer_record_invalid_rating(self):
        """Test that invalid rating raises validation error."""
        location = GeoLocation(latitude=28.6139, longitude=77.2090)
        keys = FarmerRecord.create_keys("hash123", "farmer_001", "Delhi")
        
        with pytest.raises(ValueError):
            FarmerRecord(
                **keys,
                user_id="farmer_001",
                phone_number="encrypted_phone",
                phone_hash="hash123",
                name="Test Farmer",
                location=location,
                district="Delhi",
                land_size=5.0,
                crop_types=["wheat"],
                soil_type="loamy",
                rating=6.0,  # Invalid: > 5
            )


class TestBuyerRecord:
    """Test cases for BuyerRecord."""

    def test_create_keys(self):
        """Test key creation for buyer record."""
        phone_hash = "xyz789"
        user_id = "buyer_001"
        district = "Mumbai"
        
        keys = BuyerRecord.create_keys(phone_hash, user_id, district)
        
        assert keys["PK"] == "BUYER#xyz789"
        assert keys["SK"] == "PROFILE"
        assert keys["GSI1PK"] == "DISTRICT#Mumbai"
        assert keys["GSI1SK"] == "BUYER#buyer_001"

    def test_buyer_record_creation(self):
        """Test creating a complete buyer record."""
        location = GeoLocation(latitude=19.0760, longitude=72.8777)
        keys = BuyerRecord.create_keys("hash456", "buyer_001", "Mumbai")
        
        record = BuyerRecord(
            **keys,
            user_id="buyer_001",
            phone_number="encrypted_phone",
            phone_hash="hash456",
            name="Test Buyer",
            language=Language.MARATHI,
            location=location,
            district="Mumbai",
            business_name="ABC Traders",
            crop_interests=["wheat", "rice"],
            typical_volume_quintal=1000,
            max_purchase_distance_km=50,
        )
        
        assert record.PK == "BUYER#hash456"
        assert record.SK == "PROFILE"
        assert record.business_name == "ABC Traders"
        assert record.typical_volume_quintal == 1000
        assert record.verified is False

    def test_buyer_record_with_optional_fields(self):
        """Test buyer record with optional fields."""
        location = GeoLocation(latitude=19.0760, longitude=72.8777)
        keys = BuyerRecord.create_keys("hash456", "buyer_001", "Mumbai")
        
        record = BuyerRecord(
            **keys,
            user_id="buyer_001",
            phone_number="encrypted_phone",
            phone_hash="hash456",
            name="Test Buyer",
            location=location,
            district="Mumbai",
            business_name="ABC Traders",
            contact_person="John Doe",
            crop_interests=["wheat"],
            typical_volume_quintal=1000,
            max_purchase_distance_km=50,
            quality_preferences=["A", "B"],
            verified=True,
            rating=4.2,
        )
        
        assert record.contact_person == "John Doe"
        assert record.quality_preferences == ["A", "B"]
        assert record.verified is True
        assert record.rating == 4.2


class TestPriceCacheRecord:
    """Test cases for PriceCacheRecord."""

    def test_create_keys(self):
        """Test key creation for price cache record."""
        crop = "wheat"
        district = "Delhi"
        date = datetime(2024, 1, 15)
        
        keys = PriceCacheRecord.create_keys(crop, district, date)
        
        assert keys["PK"] == "PRICE#wheat#Delhi"
        assert keys["SK"] == "DATE#2024-01-15"

    def test_calculate_ttl(self):
        """Test TTL calculation."""
        timestamp = datetime(2024, 1, 15, 12, 0, 0)
        ttl = PriceCacheRecord.calculate_ttl(timestamp, hours=24)
        
        expected_expiry = timestamp + timedelta(hours=24)
        expected_ttl = int(expected_expiry.timestamp())
        
        assert ttl == expected_ttl

    def test_price_cache_record_creation(self):
        """Test creating a complete price cache record."""
        location = GeoLocation(latitude=28.6139, longitude=77.2090)
        date = datetime(2024, 1, 15)
        keys = PriceCacheRecord.create_keys("wheat", "Delhi", date)
        timestamp = datetime.utcnow()
        
        record = PriceCacheRecord(
            **keys,
            crop="wheat",
            variety="HD-2967",
            mandi_name="Azadpur Mandi",
            location=location,
            district="Delhi",
            price_per_quintal=2500.0,
            timestamp=timestamp,
            source="Agmarknet",
            TTL=PriceCacheRecord.calculate_ttl(timestamp),
        )
        
        assert record.PK == "PRICE#wheat#Delhi"
        assert record.crop == "wheat"
        assert record.price_per_quintal == 2500.0
        assert record.source == "Agmarknet"
        assert isinstance(record.TTL, int)


class TestQueryLogRecord:
    """Test cases for QueryLogRecord."""

    def test_create_keys(self):
        """Test key creation for query log record."""
        user_id = "farmer_001"
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        keys = QueryLogRecord.create_keys(user_id, timestamp)
        
        assert keys["PK"] == "USER#farmer_001"
        assert "QUERY#2024-01-15" in keys["SK"]

    def test_query_log_record_creation(self):
        """Test creating a complete query log record."""
        timestamp = datetime.utcnow()
        keys = QueryLogRecord.create_keys("farmer_001", timestamp)
        
        record = QueryLogRecord(
            **keys,
            query_id="query_123",
            user_id="farmer_001",
            query="What is the price of wheat?",
            intent="PRICE_QUERY",
            channel="SMS",
            language=Language.HINDI,
            response="Current wheat price is 2500 INR per quintal",
            response_time_ms=250,
            timestamp=timestamp,
        )
        
        assert record.PK == "USER#farmer_001"
        assert record.query_id == "query_123"
        assert record.intent == "PRICE_QUERY"
        assert record.channel == "SMS"
        assert record.response_time_ms == 250

    def test_query_log_record_with_session(self):
        """Test query log record with session ID."""
        timestamp = datetime.utcnow()
        keys = QueryLogRecord.create_keys("farmer_001", timestamp)
        
        record = QueryLogRecord(
            **keys,
            query_id="query_123",
            user_id="farmer_001",
            query="What is the price of wheat?",
            intent="PRICE_QUERY",
            channel="IVR",
            language=Language.HINDI,
            response="Current wheat price is 2500 INR per quintal",
            response_time_ms=250,
            timestamp=timestamp,
            session_id="session_abc",
        )
        
        assert record.session_id == "session_abc"


class TestConversationRecord:
    """Test cases for ConversationRecord."""

    def test_create_keys(self):
        """Test key creation for conversation record."""
        session_id = "session_abc"
        turn_number = 3
        
        keys = ConversationRecord.create_keys(session_id, turn_number)
        
        assert keys["PK"] == "SESSION#session_abc"
        assert keys["SK"] == "TURN#0003"  # Zero-padded

    def test_create_keys_zero_padding(self):
        """Test that turn numbers are zero-padded correctly."""
        keys1 = ConversationRecord.create_keys("session_abc", 1)
        keys2 = ConversationRecord.create_keys("session_abc", 99)
        keys3 = ConversationRecord.create_keys("session_abc", 1000)
        
        assert keys1["SK"] == "TURN#0001"
        assert keys2["SK"] == "TURN#0099"
        assert keys3["SK"] == "TURN#1000"

    def test_calculate_ttl(self):
        """Test TTL calculation for conversations."""
        timestamp = datetime(2024, 1, 15, 12, 0, 0)
        ttl = ConversationRecord.calculate_ttl(timestamp, hours=1)
        
        expected_expiry = timestamp + timedelta(hours=1)
        expected_ttl = int(expected_expiry.timestamp())
        
        assert ttl == expected_ttl

    def test_conversation_record_creation(self):
        """Test creating a complete conversation record."""
        timestamp = datetime.utcnow()
        keys = ConversationRecord.create_keys("session_abc", 1)
        
        record = ConversationRecord(
            **keys,
            session_id="session_abc",
            user_id="farmer_001",
            turn_number=1,
            user_message="What is the price of wheat?",
            assistant_message="Current wheat price is 2500 INR per quintal",
            intent="PRICE_QUERY",
            timestamp=timestamp,
            TTL=ConversationRecord.calculate_ttl(timestamp),
        )
        
        assert record.PK == "SESSION#session_abc"
        assert record.SK == "TURN#0001"
        assert record.turn_number == 1
        assert record.user_message == "What is the price of wheat?"
        assert isinstance(record.TTL, int)


class TestDynamoDBTables:
    """Test cases for DYNAMODB_TABLES configuration."""

    def test_all_tables_defined(self):
        """Test that all required tables are defined."""
        expected_tables = [
            "farmers",
            "buyers",
            "price_cache",
            "query_logs",
            "conversations",
        ]
        
        for table in expected_tables:
            assert table in DYNAMODB_TABLES

    def test_farmers_table_structure(self):
        """Test farmers table structure."""
        table = DYNAMODB_TABLES["farmers"]
        
        assert table["table_name"] == "agribridge-farmers"
        assert table["partition_key"]["name"] == "PK"
        assert table["partition_key"]["type"] == "S"
        assert table["sort_key"]["name"] == "SK"
        assert len(table["gsi"]) == 1
        assert table["gsi"][0]["name"] == "GSI1"
        assert table["ttl_attribute"] is None

    def test_price_cache_table_has_ttl(self):
        """Test that price cache table has TTL configured."""
        table = DYNAMODB_TABLES["price_cache"]
        
        assert table["ttl_attribute"] == "TTL"

    def test_conversations_table_has_ttl(self):
        """Test that conversations table has TTL configured."""
        table = DYNAMODB_TABLES["conversations"]
        
        assert table["ttl_attribute"] == "TTL"

    def test_query_logs_table_no_gsi(self):
        """Test that query logs table has no GSI."""
        table = DYNAMODB_TABLES["query_logs"]
        
        assert len(table["gsi"]) == 0
