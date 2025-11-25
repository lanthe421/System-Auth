"""Property-based tests for JWT token utilities."""

import pytest
from hypothesis import given, strategies as st, settings
from app.utils.jwt import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    get_user_id_from_token
)


# Feature: auth-system, Property 8: Token-based user identification
# Validates: Requirements 2.5
@given(user_id=st.integers(min_value=1, max_value=1000000))
@settings(max_examples=100)
def test_property_8_token_based_user_identification(user_id):
    """
    Property 8: Token-based user identification
    
    For any authenticated user making multiple requests with the same valid token,
    the system should consistently identify the same user without requiring 
    re-authentication.
    
    Validates: Requirements 2.5
    """
    # Generate an access token for the user
    token = generate_access_token(user_id)
    
    # Verify the token multiple times (simulating multiple requests)
    for _ in range(5):
        # Each verification should return the same user ID
        extracted_user_id = get_user_id_from_token(token)
        assert extracted_user_id == user_id, \
            f"Token should consistently identify user {user_id}, got {extracted_user_id}"
        
        # Verify token should return valid payload
        payload = verify_token(token)
        assert payload is not None, "Token should be valid"
        assert payload.get("type") == "access", "Token type should be 'access'"
        assert int(payload.get("sub")) == user_id, \
            f"Token payload should contain user ID {user_id}"
    
    # The same token should work for refresh tokens too
    refresh_token = generate_refresh_token(user_id)
    
    # Verify refresh token multiple times
    for _ in range(5):
        payload = verify_token(refresh_token, token_type="refresh")
        assert payload is not None, "Refresh token should be valid"
        assert payload.get("type") == "refresh", "Token type should be 'refresh'"
        assert int(payload.get("sub")) == user_id, \
            f"Refresh token payload should contain user ID {user_id}"
