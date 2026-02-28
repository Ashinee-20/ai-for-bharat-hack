"""Authentication service for OTP generation, verification, and JWT token management."""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import boto3
from botocore.exceptions import ClientError

from src.models.auth import OTPRecord, OTPRequest, OTPVerifyRequest, OTPResponse, AuthResponse
from src.models.user import AuthToken, UserProfile
from src.models.common import UserType
from src.utils.security import get_phone_hasher
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        """Initialize authentication service."""
        self.config = get_config()
        self.phone_hasher = get_phone_hasher()
        
        # Initialize AWS SNS client for SMS
        sns_config = {
            "region_name": self.config.aws_region,
        }
        if self.config.sns_endpoint_url:
            sns_config["endpoint_url"] = self.config.sns_endpoint_url
        if self.config.aws_access_key_id:
            sns_config["aws_access_key_id"] = self.config.aws_access_key_id
        if self.config.aws_secret_access_key:
            sns_config["aws_secret_access_key"] = self.config.aws_secret_access_key
            
        self.sns_client = boto3.client("sns", **sns_config)
        
        # Initialize DynamoDB client for OTP storage
        dynamodb_config = {
            "region_name": self.config.aws_region,
        }
        if self.config.dynamodb_endpoint_url:
            dynamodb_config["endpoint_url"] = self.config.dynamodb_endpoint_url
        if self.config.aws_access_key_id:
            dynamodb_config["aws_access_key_id"] = self.config.aws_access_key_id
        if self.config.aws_secret_access_key:
            dynamodb_config["aws_secret_access_key"] = self.config.aws_secret_access_key
            
        self.dynamodb = boto3.resource("dynamodb", **dynamodb_config)
        self.otp_table_name = f"{self.config.dynamodb_table_prefix}-otp"
        
    def generate_otp(self) -> str:
        """Generate a 6-digit random OTP code.
        
        Returns:
            6-digit OTP string
        """
        # Generate cryptographically secure random 6-digit number
        otp = secrets.randbelow(1000000)
        # Zero-pad to ensure 6 digits
        return f"{otp:06d}"
    
    def hash_otp(self, otp: str) -> str:
        """Hash an OTP code using HMAC-SHA256.
        
        Args:
            otp: OTP code to hash
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hmac.new(
            key=self.config.jwt_secret_key.encode('utf-8'),
            msg=otp.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        return hash_obj.hexdigest()
    
    def verify_otp_hash(self, otp: str, otp_hash: str) -> bool:
        """Verify if an OTP matches its hash.
        
        Args:
            otp: OTP code to verify
            otp_hash: Expected hash value
            
        Returns:
            True if OTP matches hash, False otherwise
        """
        computed_hash = self.hash_otp(otp)
        return hmac.compare_digest(computed_hash, otp_hash)
    
    async def send_otp(self, request: OTPRequest) -> OTPResponse:
        """Send OTP to a phone number via SMS.
        
        Args:
            request: OTP request with phone number
            
        Returns:
            OTP response indicating success or failure
        """
        try:
            # Generate OTP
            otp = self.generate_otp()
            logger.info(f"Generated OTP for phone number (last 4 digits): ...{request.phone_number[-4:]}")
            
            # Hash phone number and OTP
            phone_hash = self.phone_hasher.hash_phone_number(request.phone_number)
            otp_hash = self.hash_otp(otp)
            
            # Create OTP record
            otp_record = OTPRecord.create(
                phone_hash=phone_hash,
                otp_hash=otp_hash,
                expiry_minutes=10
            )
            
            # Store OTP in DynamoDB
            table = self.dynamodb.Table(self.otp_table_name)
            ttl = int(otp_record.expires_at.timestamp())
            
            table.put_item(
                Item={
                    "PK": f"OTP#{phone_hash}",
                    "SK": "CURRENT",
                    "otp_hash": otp_hash,
                    "attempts": 0,
                    "created_at": otp_record.created_at.isoformat(),
                    "expires_at": otp_record.expires_at.isoformat(),
                    "TTL": ttl
                }
            )
            
            # Send SMS via AWS SNS
            message = f"Your AgriBridge verification code is: {otp}. Valid for 10 minutes. Do not share this code."
            
            try:
                response = self.sns_client.publish(
                    PhoneNumber=request.phone_number,
                    Message=message,
                    MessageAttributes={
                        'AWS.SNS.SMS.SMSType': {
                            'DataType': 'String',
                            'StringValue': 'Transactional'
                        }
                    }
                )
                logger.info(f"SMS sent successfully. MessageId: {response.get('MessageId')}")
                
                return OTPResponse(
                    success=True,
                    message="OTP sent successfully",
                    expires_in_minutes=10
                )
                
            except ClientError as e:
                logger.error(f"Failed to send SMS: {e}")
                # In development, we might want to return the OTP for testing
                if self.config.is_local:
                    logger.warning(f"Development mode: OTP is {otp}")
                    return OTPResponse(
                        success=True,
                        message=f"OTP generated (dev mode): {otp}",
                        expires_in_minutes=10
                    )
                raise
                
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return OTPResponse(
                success=False,
                message="Failed to send OTP. Please try again."
            )
    
    async def verify_otp(self, request: OTPVerifyRequest) -> AuthResponse:
        """Verify OTP and generate JWT token upon success.
        
        Args:
            request: OTP verification request
            
        Returns:
            Authentication response with token if successful
        """
        try:
            # Hash phone number
            phone_hash = self.phone_hasher.hash_phone_number(request.phone_number)
            
            # Retrieve OTP record from DynamoDB
            table = self.dynamodb.Table(self.otp_table_name)
            response = table.get_item(
                Key={
                    "PK": f"OTP#{phone_hash}",
                    "SK": "CURRENT"
                }
            )
            
            if "Item" not in response:
                logger.warning(f"No OTP found for phone hash: {phone_hash[:8]}...")
                return AuthResponse(
                    success=False,
                    message="Invalid or expired OTP"
                )
            
            item = response["Item"]
            
            # Parse OTP record
            otp_record = OTPRecord(
                phone_hash=phone_hash,
                otp_hash=item["otp_hash"],
                attempts=item["attempts"],
                created_at=datetime.fromisoformat(item["created_at"]),
                expires_at=datetime.fromisoformat(item["expires_at"])
            )
            
            # Check if OTP is expired
            if otp_record.is_expired():
                logger.warning(f"Expired OTP for phone hash: {phone_hash[:8]}...")
                # Delete expired OTP
                table.delete_item(
                    Key={
                        "PK": f"OTP#{phone_hash}",
                        "SK": "CURRENT"
                    }
                )
                return AuthResponse(
                    success=False,
                    message="OTP has expired. Please request a new one."
                )
            
            # Check if OTP is locked due to too many attempts
            if otp_record.is_locked():
                logger.warning(f"OTP locked due to too many attempts for phone hash: {phone_hash[:8]}...")
                return AuthResponse(
                    success=False,
                    message="Too many failed attempts. Please request a new OTP."
                )
            
            # Verify OTP
            if not self.verify_otp_hash(request.otp, otp_record.otp_hash):
                # Increment attempts
                otp_record.increment_attempts()
                table.update_item(
                    Key={
                        "PK": f"OTP#{phone_hash}",
                        "SK": "CURRENT"
                    },
                    UpdateExpression="SET attempts = :attempts",
                    ExpressionAttributeValues={
                        ":attempts": otp_record.attempts
                    }
                )
                
                remaining_attempts = 3 - otp_record.attempts
                logger.warning(f"Invalid OTP attempt for phone hash: {phone_hash[:8]}... ({remaining_attempts} attempts remaining)")
                
                if remaining_attempts > 0:
                    return AuthResponse(
                        success=False,
                        message=f"Invalid OTP. {remaining_attempts} attempt(s) remaining."
                    )
                else:
                    return AuthResponse(
                        success=False,
                        message="Too many failed attempts. Please request a new OTP."
                    )
            
            # OTP verified successfully - delete it
            table.delete_item(
                Key={
                    "PK": f"OTP#{phone_hash}",
                    "SK": "CURRENT"
                }
            )
            
            # Generate JWT token
            user_id = phone_hash[:16]  # Use first 16 chars of phone hash as user ID
            token_data = self.generate_jwt_token(
                user_id=user_id,
                phone_number=request.phone_number,
                user_type=UserType.FARMER  # Default to farmer, can be updated later
            )
            
            logger.info(f"OTP verified successfully for user: {user_id}")
            
            return AuthResponse(
                success=True,
                message="Authentication successful",
                token=token_data.token,
                expires_at=token_data.expires_at,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return AuthResponse(
                success=False,
                message="Verification failed. Please try again."
            )
    
    def generate_jwt_token(
        self,
        user_id: str,
        phone_number: str,
        user_type: UserType
    ) -> AuthToken:
        """Generate JWT authentication token.
        
        Args:
            user_id: User identifier
            phone_number: User phone number
            user_type: Type of user (farmer/buyer)
            
        Returns:
            AuthToken with JWT and expiration
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.config.jwt_expiration_hours)
        
        payload = {
            "user_id": user_id,
            "phone_number": phone_number,
            "user_type": user_type.value,
            "iat": now,
            "exp": expires_at
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        return AuthToken(
            token=token,
            expires_at=expires_at,
            user_id=user_id,
            user_type=user_type
        )
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and extract payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Invalid or expired token: {e}")
            return None
