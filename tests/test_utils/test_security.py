"""Unit tests for security utilities."""

import pytest
from src.utils.security import PhoneNumberHasher, generate_salt, get_phone_hasher


class TestPhoneNumberHasher:
    """Test cases for PhoneNumberHasher."""

    def test_hash_phone_number_basic(self):
        """Test basic phone number hashing."""
        hasher = PhoneNumberHasher(salt="test_salt")
        phone = "+919876543210"
        
        hash1 = hasher.hash_phone_number(phone)
        
        # Hash should be a hex string
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_hash_phone_number_consistency(self):
        """Test that same phone number produces same hash."""
        hasher = PhoneNumberHasher(salt="test_salt")
        phone = "+919876543210"
        
        hash1 = hasher.hash_phone_number(phone)
        hash2 = hasher.hash_phone_number(phone)
        
        assert hash1 == hash2

    def test_hash_phone_number_normalization(self):
        """Test that different formats of same number produce same hash."""
        hasher = PhoneNumberHasher(salt="test_salt")
        
        # Different formats of the same number
        formats = [
            "+919876543210",
            "919876543210",
            "9876543210",
            "+91 9876543210",
            "+91-987-654-3210",
        ]
        
        hashes = [hasher.hash_phone_number(phone) for phone in formats]
        
        # All should produce the same hash
        assert len(set(hashes)) == 1

    def test_hash_phone_number_different_numbers(self):
        """Test that different phone numbers produce different hashes."""
        hasher = PhoneNumberHasher(salt="test_salt")
        
        phone1 = "+919876543210"
        phone2 = "+919876543211"
        
        hash1 = hasher.hash_phone_number(phone1)
        hash2 = hasher.hash_phone_number(phone2)
        
        assert hash1 != hash2

    def test_hash_phone_number_different_salts(self):
        """Test that same number with different salts produces different hashes."""
        phone = "+919876543210"
        
        hasher1 = PhoneNumberHasher(salt="salt1")
        hasher2 = PhoneNumberHasher(salt="salt2")
        
        hash1 = hasher1.hash_phone_number(phone)
        hash2 = hasher2.hash_phone_number(phone)
        
        assert hash1 != hash2

    def test_hash_phone_number_empty_raises_error(self):
        """Test that empty phone number raises ValueError."""
        hasher = PhoneNumberHasher(salt="test_salt")
        
        with pytest.raises(ValueError, match="Phone number cannot be empty"):
            hasher.hash_phone_number("")

    def test_verify_phone_number_correct(self):
        """Test verification with correct phone number."""
        hasher = PhoneNumberHasher(salt="test_salt")
        phone = "+919876543210"
        
        hash_value = hasher.hash_phone_number(phone)
        
        assert hasher.verify_phone_number(phone, hash_value) is True

    def test_verify_phone_number_incorrect(self):
        """Test verification with incorrect phone number."""
        hasher = PhoneNumberHasher(salt="test_salt")
        phone1 = "+919876543210"
        phone2 = "+919876543211"
        
        hash_value = hasher.hash_phone_number(phone1)
        
        assert hasher.verify_phone_number(phone2, hash_value) is False

    def test_verify_phone_number_different_formats(self):
        """Test verification works with different phone number formats."""
        hasher = PhoneNumberHasher(salt="test_salt")
        phone1 = "+919876543210"
        phone2 = "9876543210"  # Same number, different format
        
        hash_value = hasher.hash_phone_number(phone1)
        
        assert hasher.verify_phone_number(phone2, hash_value) is True

    def test_verify_phone_number_invalid_hash(self):
        """Test verification with invalid hash returns False."""
        hasher = PhoneNumberHasher(salt="test_salt")
        phone = "+919876543210"
        
        assert hasher.verify_phone_number(phone, "invalid_hash") is False

    def test_normalize_phone_number_removes_non_digits(self):
        """Test that normalization removes non-digit characters."""
        hasher = PhoneNumberHasher(salt="test_salt")
        
        phone = "+91-987-654-3210"
        normalized = hasher._normalize_phone_number(phone)
        
        assert normalized == "9876543210"
        assert normalized.isdigit()

    def test_normalize_phone_number_removes_country_code(self):
        """Test that normalization removes country code."""
        hasher = PhoneNumberHasher(salt="test_salt")
        
        # With country code
        phone1 = "919876543210"
        normalized1 = hasher._normalize_phone_number(phone1)
        assert normalized1 == "9876543210"
        
        # Without country code
        phone2 = "9876543210"
        normalized2 = hasher._normalize_phone_number(phone2)
        assert normalized2 == "9876543210"
        
        # Both should be the same
        assert normalized1 == normalized2


class TestGenerateSalt:
    """Test cases for generate_salt function."""

    def test_generate_salt_default_length(self):
        """Test salt generation with default length."""
        salt = generate_salt()
        
        assert isinstance(salt, str)
        assert len(salt) == 64  # 32 bytes = 64 hex characters

    def test_generate_salt_custom_length(self):
        """Test salt generation with custom length."""
        salt = generate_salt(length=16)
        
        assert isinstance(salt, str)
        assert len(salt) == 32  # 16 bytes = 32 hex characters

    def test_generate_salt_uniqueness(self):
        """Test that generated salts are unique."""
        salts = [generate_salt() for _ in range(10)]
        
        # All salts should be unique
        assert len(set(salts)) == 10

    def test_generate_salt_hex_format(self):
        """Test that generated salt is valid hex."""
        salt = generate_salt()
        
        # Should be valid hex string
        assert all(c in "0123456789abcdef" for c in salt)


class TestGetPhoneHasher:
    """Test cases for get_phone_hasher singleton."""

    def test_get_phone_hasher_returns_instance(self):
        """Test that get_phone_hasher returns a PhoneNumberHasher instance."""
        hasher = get_phone_hasher()
        
        assert isinstance(hasher, PhoneNumberHasher)

    def test_get_phone_hasher_singleton(self):
        """Test that get_phone_hasher returns the same instance."""
        hasher1 = get_phone_hasher()
        hasher2 = get_phone_hasher()
        
        assert hasher1 is hasher2

    def test_get_phone_hasher_functional(self):
        """Test that the global hasher works correctly."""
        hasher = get_phone_hasher()
        phone = "+919876543210"
        
        hash_value = hasher.hash_phone_number(phone)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64
