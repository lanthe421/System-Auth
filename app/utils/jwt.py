"""JWT token generation and validation utilities."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from app.config import settings


def generate_access_token(user_id: int, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a JWT access token for a user.
    
    Args:
        user_id: The ID of the user
        additional_claims: Optional additional claims to include in the token
        
    Returns:
        The encoded JWT token as a string
        
    Requirements: 2.1, 2.5, 3.1
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "iat": now,  # Issued at
        "exp": expires_at,  # Expiration time
        "type": "access"
    }
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def generate_refresh_token(user_id: int) -> str:
    """
    Generate a JWT refresh token for a user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        The encoded JWT refresh token as a string
        
    Requirements: 2.1, 3.1
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
        "type": "refresh"
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        token_type: The expected token type ("access" or "refresh")
        
    Returns:
        The decoded token payload if valid, None otherwise
        
    Requirements: 2.5, 3.1
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Token is invalid
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from a valid token.
    
    Args:
        token: The JWT token
        
    Returns:
        The user ID if token is valid, None otherwise
        
    Requirements: 2.5
    """
    payload = verify_token(token)
    if payload:
        try:
            return int(payload.get("sub"))
        except (ValueError, TypeError):
            return None
    return None
