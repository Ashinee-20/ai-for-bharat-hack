"""Unit tests for authentication service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.services.auth_service import AuthService
from src.models.auth import OTPRequest, OTPVerifyRequest, OTPResponse, AuthResponse
from src.models.common import UserType


@pytest.fixture
def auth_service():
    """Create auth service instance for testing."""
    with patch('src.services.auth_service.boto3'):
        service = AuthService()
        # Mock the DynamoDB table
        service.dynamodb = MagicMock()
        service.sns_client = MagicMock()
        return service


class TestOTPGeneration:
    """Test cases for OTP generation."""

    def test_generate_otp_format(self, auth_service):
        """Test that generated OTP is 6 digits."""
        otp = auth_service.generate_otp()
        
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_otp_uniqueness(self, auth_service):
        """Test that generated OTPs are unique."""
        otps = [auth_service.generate_otp() for _ in range(100)]
        
        # Most should be unique (allowing for rare collisions)
        assert len(set(otps)) > 95

    def test_generate_otp_zero_padding(self, auth_service):
        """Test that OTP is zero-padded to 6 digits."""
        # Generate many OTPs to likely get some with leading zeros
        otps = [auth_service.generate_otp() for _ in range(1000)]
        
        # All should be exactly 6 characters
        assert all(len(otp) == 6 for otp in otps)
        # Some should start with 0 (statistically)
        assert any(otp.startswith('0') for otp in otps)


class TestOTPHashing:
    """Test cases for OTP hashing."""

    def test_hash_otp_consistency(self, auth_service):
        """Test that same OTP produces same hash."""
        otp = "123456"
        
        hash1 = auth_service.hash_otp(otp)
        hash2 = auth_service.hash_otp(otp)
        
        assert hash1 == hash2

    def test_hash_otp_different_otps(self, auth_service):
        """Test that different OTPs produce different hashes."""
        otp1 = "123456"
        otp2 = "654321"
        
        hash1 = auth_service.hash_otp(otp1)
        hash2 = auth_service.hash_otp(otp2)
        
        assert hash1 != hash2

    def test_hash_otp_format(self, auth_service):
        """Test that hash is valid hex string."""
        otp = "123456"
        
        hash_value = auth_service.hash_otp(otp)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_verify_otp_hash_correct(self, auth_service):
        """Test verification with correct OTP."""
        otp = "123456"
        otp_hash = auth_service.hash_otp(otp)
        
        assert auth_service.verify_otp_hash(otp, otp_hash) is True

    def test_verify_otp_hash_incorrect(self, auth_service):
        """Test verification with incorrect OTP."""
        otp1 = "123456"
        otp2 = "654321"
        otp_hash = auth_service.hash_otp(otp1)
        
        assert auth_service.verify_otp_hash(otp2, otp_hash) is False


class TestSendOTP:
    """Test cases for sending OTP."""

    @pytest.mark.asyncio
    async def test_send_otp_success(self, auth_service):
        """Test successful OTP sending."""
        # Mock DynamoDB table
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        
        # Mock SNS client
        auth_service.sns_client.publish.return_value = {
            'MessageId': 'test-message-id'
        }
        
        request = OTPRequest(phone_number="+919876543210")
        response = await auth_service.send_otp(request)
        
        assert response.success is True
        assert response.expires_in_minutes == 10
        assert "successfully" in response.message.lower()
        
        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()
        
        # Verify SNS publish was called
        auth_service.sns_client.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_otp_stores_in_dynamodb(self, auth_service):
        """Test that OTP is stored in DynamoDB."""
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        auth_service.sns_client.publish.return_value = {'MessageId': 'test-id'}
        
        request = OTPRequest(phone_number="+919876543210")
        await auth_service.send_otp(request)
        
        # Verify put_item was called with correct structure
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs['Item']
        
        assert 'PK' in item
        assert item['PK'].startswith('OTP#')
        assert item['SK'] == 'CURRENT'
        assert 'otp_hash' in item
        assert 'attempts' in item
        assert item['attempts'] == 0
        assert 'TTL' in item

    @pytest.mark.asyncio
    async def test_send_otp_sns_failure_dev_mode(self, auth_service):
        """Test OTP sending when SNS fails in dev mode."""
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        
        # Mock SNS failure
        auth_service.sns_client.publish.side_effect = ClientError(
            {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
            'publish'
        )
        
        # Set to local mode
        auth_service.config.is_local = True
        
        request = OTPRequest(phone_number="+919876543210")
        response = await auth_service.send_otp(request)
        
        # Should still succeed in dev mode
        assert response.success is True
        assert "dev mode" in response.message.lower()


class TestVerifyOTP:
    """Test cases for OTP verification."""

    @pytest.mark.asyncio
    async def test_verify_otp_success(self, auth_service):
        """Test successful OTP verification."""
        phone_number = "+919876543210"
        otp = "123456"
        
        # Hash the OTP
        otp_hash = auth_service.hash_otp(otp)
        phone_hash = auth_service.phone_hasher.hash_phone_number(phone_number)
        
        # Mock DynamoDB responses
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        
        # Mock get_item to return OTP record
        future_time = datetime.utcnow() + timedelta(minutes=5)
        mock_table.get_item.return_value = {
            'Item': {
                'PK': f'OTP#{phone_hash}',
                'SK': 'CURRENT',
                'otp_hash': otp_hash,
                'attempts': 0,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': future_time.isoformat()
            }
        }
        
        request = OTPVerifyRequest(phone_number=phone_number, otp=otp)
        response = await auth_service.verify_otp(request)
        
        assert response.success is True
        assert response.token is not None
        assert response.user_id is not None
        assert response.expires_at is not None
        
        # Verify OTP was deleted after successful verification
        mock_table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_otp_not_found(self, auth_service):
        """Test OTP verification when OTP doesn't exist."""
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        
        # Mock get_item to return no item
        mock_table.get_item.return_value = {}
        
        request = OTPVerifyRequest(phone_number="+919876543210", otp="123456")
        response = await auth_service.verify_otp(request)
        
        assert response.success is False
        assert "invalid" in response.message.lower() or "expired" in response.message.lower()

    @pytest.mark.asyncio
    async def test_verify_otp_expired(self, auth_service):
        """Test OTP verification when OTP has expired."""
        phone_number = "+919876543210"
        otp = "123456"
        otp_hash = auth_service.hash_otp(otp)
        phone_hash = auth_service.phone_hasher.hash_phone_number(phone_number)
        
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        
        # Mock get_item to return expired OTP
        past_time = datetime.utcnow() - timedelta(minutes=5)
        mock_table.get_item.return_value = {
            'Item': {
                'PK': f'OTP#{phone_hash}',
                'SK': 'CURRENT',
                'otp_hash': otp_hash,
                'attempts': 0,
                'created_at': (past_time - timedelta(minutes=10)).isoformat(),
                'expires_at': past_time.isoformat()
            }
        }
        
        request = OTPVerifyRequest(phone_number=phone_number, otp=otp)
        response = await auth_service.verify_otp(request)
        
        assert response.success is False
        assert "expired" in response.message.lower()
        
        # Verify expired OTP was deleted
        mock_table.delete_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_otp_incorrect(self, auth_service):
        """Test OTP verification with incorrect OTP."""
        phone_number = "+919876543210"
        correct_otp = "123456"
        incorrect_otp = "654321"
        
        otp_hash = auth_service.hash_otp(correct_otp)
        phone_hash = auth_service.phone_hasher.hash_phone_number(phone_number)
        
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        
        future_time = datetime.utcnow() + timedelta(minutes=5)
        mock_table.get_item.return_value = {
            'Item': {
                'PK': f'OTP#{phone_hash}',
                'SK': 'CURRENT',
                'otp_hash': otp_hash,
                'attempts': 0,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': future_time.isoformat()
            }
        }
        
        request = OTPVerifyRequest(phone_number=phone_number, otp=incorrect_otp)
        response = await auth_service.verify_otp(request)
        
        assert response.success is False
        assert "invalid" in response.message.lower()
        assert "attempt" in response.message.lower()
        
        # Verify attempts were incremented
        mock_table.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_otp_max_attempts(self, auth_service):
        """Test OTP verification when max attempts reached."""
        phone_number = "+919876543210"
        otp = "123456"
        otp_hash = auth_service.hash_otp(otp)
        phone_hash = auth_service.phone_hasher.hash_phone_number(phone_number)
        
        mock_table = MagicMock()
        auth_service.dynamodb.Table.return_value = mock_table
        
        future_time = datetime.utcnow() + timedelta(minutes=5)
        mock_table.get_item.return_value = {
            'Item': {
                'PK': f'OTP#{phone_hash}',
                'SK': 'CURRENT',
                'otp_hash': otp_hash,
                'attempts': 3,  # Max attempts reached
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': future_time.isoformat()
            }
        }
        
        request = OTPVerifyRequest(phone_number=phone_number, otp=otp)
        response = await auth_service.verify_otp(request)
        
        assert response.success is False
        assert "too many" in response.message.lower()


class TestJWTToken:
    """Test cases for JWT token generation and validation."""

    def test_generate_jwt_token(self, auth_service):
        """Test JWT token generation."""
        user_id = "test_user_123"
        phone_number = "+919876543210"
        user_type = UserType.FARMER
        
        token_data = auth_service.generate_jwt_token(user_id, phone_number, user_type)
        
        assert token_data.token is not None
        assert isinstance(token_data.token, str)
        assert token_data.user_id == user_id
        assert token_data.user_type == user_type
        assert token_data.expires_at > datetime.utcnow()

    def test_validate_token_success(self, auth_service):
        """Test successful token validation."""
        user_id = "test_user_123"
        phone_number = "+919876543210"
        user_type = UserType.FARMER
        
        token_data = auth_service.generate_jwt_token(user_id, phone_number, user_type)
        
        payload = auth_service.validate_token(token_data.token)
        
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['phone_number'] == phone_number
        assert payload['user_type'] == user_type.value

    def test_validate_token_invalid(self, auth_service):
        """Test validation of invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = auth_service.validate_token(invalid_token)
        
        assert payload is None

    def test_validate_token_expired(self, auth_service):
        """Test validation of expired token."""
        # Temporarily set expiration to 0 hours
        original_expiration = auth_service.config.jwt_expiration_hours
        auth_service.config.jwt_expiration_hours = 0
        
        user_id = "test_user_123"
        phone_number = "+919876543210"
        user_type = UserType.FARMER
        
        token_data = auth_service.generate_jwt_token(user_id, phone_number, user_type)
        
        # Restore original expiration
        auth_service.config.jwt_expiration_hours = original_expiration
        
        # Token should be expired
        payload = auth_service.validate_token(token_data.token)
        
        assert payload is None

    def test_jwt_token_contains_required_fields(self, auth_service):
        """Test that JWT token contains all required fields."""
        user_id = "test_user_123"
        phone_number = "+919876543210"
        user_type = UserType.FARMER
        
        token_data = auth_service.generate_jwt_token(user_id, phone_number, user_type)
        payload = auth_service.validate_token(token_data.token)
        
        assert 'user_id' in payload
        assert 'phone_number' in payload
        assert 'user_type' in payload
        assert 'iat' in payload  # Issued at
        assert 'exp' in payload  # Expiration
