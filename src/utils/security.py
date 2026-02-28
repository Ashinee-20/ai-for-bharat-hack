"""Security utilities for encryption, hashing, and data protection."""

import base64
import hashlib
import hmac
import secrets
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from .config import get_config
from .logger import get_logger

logger = get_logger(__name__)


class PhoneNumberHasher:
    """Utility for securely hashing phone numbers with salt."""

    def __init__(self, salt: Optional[str] = None):
        """Initialize phone number hasher.
        
        Args:
            salt: Optional salt value. If not provided, uses config or generates one.
        """
        config = get_config()
        self._salt = salt or config.jwt_secret_key  # Use JWT secret as salt for now
        
    def hash_phone_number(self, phone_number: str) -> str:
        """Hash a phone number using HMAC-SHA256 with salt.
        
        Args:
            phone_number: Phone number to hash (should be normalized)
            
        Returns:
            Hexadecimal hash string
            
        Raises:
            ValueError: If phone number is empty
        """
        if not phone_number:
            raise ValueError("Phone number cannot be empty")
            
        # Normalize phone number (remove spaces, dashes, etc.)
        normalized = self._normalize_phone_number(phone_number)
        
        # Use HMAC-SHA256 for secure hashing with salt
        hash_obj = hmac.new(
            key=self._salt.encode('utf-8'),
            msg=normalized.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        
        return hash_obj.hexdigest()
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number by removing non-digit characters.
        
        Args:
            phone_number: Raw phone number string
            
        Returns:
            Normalized phone number with only digits
        """
        # Remove all non-digit characters
        normalized = ''.join(c for c in phone_number if c.isdigit())
        
        # Remove leading country code if present (e.g., 91 for India)
        if normalized.startswith('91') and len(normalized) > 10:
            normalized = normalized[2:]
            
        return normalized
    
    def verify_phone_number(self, phone_number: str, hash_value: str) -> bool:
        """Verify if a phone number matches a hash.
        
        Args:
            phone_number: Phone number to verify
            hash_value: Expected hash value
            
        Returns:
            True if phone number matches hash, False otherwise
        """
        try:
            computed_hash = self.hash_phone_number(phone_number)
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(computed_hash, hash_value)
        except (ValueError, TypeError):
            return False


def generate_salt(length: int = 32) -> str:
    """Generate a cryptographically secure random salt.
    
    Args:
        length: Length of salt in bytes
        
    Returns:
        Hexadecimal salt string
    """
    return secrets.token_hex(length)


# Global hasher instance
_phone_hasher: Optional[PhoneNumberHasher] = None


def get_phone_hasher() -> PhoneNumberHasher:
    """Get or create global phone number hasher instance.
    
    Returns:
        PhoneNumberHasher instance
    """
    global _phone_hasher
    if _phone_hasher is None:
        _phone_hasher = PhoneNumberHasher()
    return _phone_hasher



class DataEncryptor:
    """AES-256 encryption/decryption utility for data at rest."""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize data encryptor.
        
        Args:
            key: Optional 32-byte encryption key. If not provided, generates one.
        """
        if key is None:
            key = secrets.token_bytes(32)  # 256 bits
        elif len(key) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes (256 bits)")
        
        self._key = key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext using AES-256-CBC.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded string containing IV + ciphertext
            
        Raises:
            ValueError: If plaintext is empty
        """
        if not plaintext:
            raise ValueError("Plaintext cannot be empty")
        
        # Generate random IV (16 bytes for AES)
        iv = secrets.token_bytes(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad plaintext to block size (128 bits = 16 bytes)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        # Encrypt
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV + ciphertext and encode as base64
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt AES-256-CBC encrypted data.
        
        Args:
            encrypted_data: Base64-encoded string containing IV + ciphertext
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If encrypted_data is invalid or decryption fails
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")
        
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract IV (first 16 bytes) and ciphertext
            if len(data) < 16:
                raise ValueError("Invalid encrypted data: too short")
            
            iv = data[:16]
            ciphertext = data[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self._key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Decryption failed: {str(e)}")


class KMSEncryptor:
    """AWS KMS-based encryption for data at rest."""
    
    def __init__(self, kms_key_id: Optional[str] = None):
        """Initialize KMS encryptor.
        
        Args:
            kms_key_id: AWS KMS key ID or ARN. If not provided, uses config.
        """
        config = get_config()
        self._kms_key_id = kms_key_id or config.encryption_key_id
        self._kms_client = boto3.client('kms', region_name=config.aws_region)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext using AWS KMS.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded ciphertext
            
        Raises:
            ValueError: If plaintext is empty or KMS key ID not configured
            ClientError: If KMS operation fails
        """
        if not plaintext:
            raise ValueError("Plaintext cannot be empty")
        
        if not self._kms_key_id:
            raise ValueError("KMS key ID not configured")
        
        try:
            response = self._kms_client.encrypt(
                KeyId=self._kms_key_id,
                Plaintext=plaintext.encode('utf-8')
            )
            
            # Return base64-encoded ciphertext
            ciphertext_blob = response['CiphertextBlob']
            return base64.b64encode(ciphertext_blob).decode('utf-8')
        except ClientError as e:
            logger.error(f"KMS encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt KMS-encrypted data.
        
        Args:
            encrypted_data: Base64-encoded ciphertext
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If encrypted_data is invalid
            ClientError: If KMS operation fails
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")
        
        try:
            # Decode base64
            ciphertext_blob = base64.b64decode(encrypted_data.encode('utf-8'))
            
            response = self._kms_client.decrypt(
                CiphertextBlob=ciphertext_blob
            )
            
            return response['Plaintext'].decode('utf-8')
        except ClientError as e:
            logger.error(f"KMS decryption failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def generate_data_key(self) -> tuple[bytes, str]:
        """Generate a data encryption key using KMS.
        
        Returns:
            Tuple of (plaintext_key, encrypted_key_base64)
            
        Raises:
            ValueError: If KMS key ID not configured
            ClientError: If KMS operation fails
        """
        if not self._kms_key_id:
            raise ValueError("KMS key ID not configured")
        
        try:
            response = self._kms_client.generate_data_key(
                KeyId=self._kms_key_id,
                KeySpec='AES_256'
            )
            
            plaintext_key = response['Plaintext']
            encrypted_key = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
            
            return plaintext_key, encrypted_key
        except ClientError as e:
            logger.error(f"KMS data key generation failed: {str(e)}")
            raise


class DynamoDBEncryptionWrapper:
    """Wrapper for encrypting sensitive fields in DynamoDB items."""
    
    def __init__(self, encryptor: Optional[DataEncryptor] = None):
        """Initialize DynamoDB encryption wrapper.
        
        Args:
            encryptor: DataEncryptor instance. If not provided, creates one.
        """
        self._encryptor = encryptor or _get_default_encryptor()
    
    def encrypt_item(self, item: Dict[str, Any], fields_to_encrypt: list[str]) -> Dict[str, Any]:
        """Encrypt specified fields in a DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            New dictionary with encrypted fields
        """
        encrypted_item = item.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_item and encrypted_item[field]:
                # Convert to string if not already
                value = str(encrypted_item[field])
                encrypted_item[field] = self._encryptor.encrypt(value)
                # Mark field as encrypted
                encrypted_item[f"{field}_encrypted"] = True
        
        return encrypted_item
    
    def decrypt_item(self, item: Dict[str, Any], fields_to_decrypt: list[str]) -> Dict[str, Any]:
        """Decrypt specified fields in a DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary with encrypted fields
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            New dictionary with decrypted fields
        """
        decrypted_item = item.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_item and decrypted_item.get(f"{field}_encrypted"):
                try:
                    decrypted_item[field] = self._encryptor.decrypt(decrypted_item[field])
                    # Remove encryption marker
                    decrypted_item.pop(f"{field}_encrypted", None)
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {str(e)}")
                    # Keep encrypted value if decryption fails
        
        return decrypted_item


class RDSEncryptionWrapper:
    """Wrapper for encrypting sensitive fields before storing in RDS."""
    
    def __init__(self, encryptor: Optional[DataEncryptor] = None):
        """Initialize RDS encryption wrapper.
        
        Args:
            encryptor: DataEncryptor instance. If not provided, creates one.
        """
        self._encryptor = encryptor or _get_default_encryptor()
    
    def encrypt_fields(self, data: Dict[str, Any], fields_to_encrypt: list[str]) -> Dict[str, Any]:
        """Encrypt specified fields in a data dictionary.
        
        Args:
            data: Data dictionary
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            New dictionary with encrypted fields
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                # Convert to string if not already
                value = str(encrypted_data[field])
                encrypted_data[field] = self._encryptor.encrypt(value)
        
        return encrypted_data
    
    def decrypt_fields(self, data: Dict[str, Any], fields_to_decrypt: list[str]) -> Dict[str, Any]:
        """Decrypt specified fields in a data dictionary.
        
        Args:
            data: Data dictionary with encrypted fields
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            New dictionary with decrypted fields
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field] is not None:
                try:
                    decrypted_data[field] = self._encryptor.decrypt(decrypted_data[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {str(e)}")
                    # Keep encrypted value if decryption fails
        
        return decrypted_data


# Global encryptor instance
_default_encryptor: Optional[DataEncryptor] = None


def _get_default_encryptor() -> DataEncryptor:
    """Get or create default data encryptor instance.
    
    Returns:
        DataEncryptor instance
    """
    global _default_encryptor
    if _default_encryptor is None:
        # In production, this key should come from KMS or environment variable
        config = get_config()
        # Use JWT secret as encryption key for now (should be 32 bytes)
        key_material = config.jwt_secret_key.encode('utf-8')
        # Derive 32-byte key using SHA-256
        key = hashlib.sha256(key_material).digest()
        _default_encryptor = DataEncryptor(key)
    return _default_encryptor


def get_data_encryptor(key: Optional[bytes] = None) -> DataEncryptor:
    """Get data encryptor instance.
    
    Args:
        key: Optional encryption key. If not provided, uses default.
        
    Returns:
        DataEncryptor instance
    """
    if key is None:
        return _get_default_encryptor()
    return DataEncryptor(key)


def get_kms_encryptor(kms_key_id: Optional[str] = None) -> KMSEncryptor:
    """Get KMS encryptor instance.
    
    Args:
        kms_key_id: Optional KMS key ID. If not provided, uses config.
        
    Returns:
        KMSEncryptor instance
    """
    return KMSEncryptor(kms_key_id)


def get_dynamodb_encryption_wrapper(encryptor: Optional[DataEncryptor] = None) -> DynamoDBEncryptionWrapper:
    """Get DynamoDB encryption wrapper instance.
    
    Args:
        encryptor: Optional DataEncryptor instance.
        
    Returns:
        DynamoDBEncryptionWrapper instance
    """
    return DynamoDBEncryptionWrapper(encryptor)


def get_rds_encryption_wrapper(encryptor: Optional[DataEncryptor] = None) -> RDSEncryptionWrapper:
    """Get RDS encryption wrapper instance.
    
    Args:
        encryptor: Optional DataEncryptor instance.
        
    Returns:
        RDSEncryptionWrapper instance
    """
    return RDSEncryptionWrapper(encryptor)
