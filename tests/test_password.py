"""Property-based tests for password hashing utilities."""

import pytest
from hypothesis import given, strategies as st, settings
from app.utils.password import hash_password, verify_password


# Feature: auth-system, Property 4: Password hashing invariant
# Validates: Requirements 1.4, 4.3
@given(password=st.text(min_size=1, max_size=100))
@settings(max_examples=100, deadline=None)  # No deadline since bcrypt is intentionally slow
def test_property_4_password_hashing_invariant(password):
    """
    Property 4: Password hashing invariant
    
    For any password (during registration or update), the stored password_hash 
    in the database should never equal the plaintext password and should be 
    verifiable using the hashing algorithm.
    
    Validates: Requirements 1.4, 4.3
    """
    # Hash the password
    password_hash = hash_password(password)
    
    # The hash should never equal the plaintext password
    assert password_hash != password, "Password hash should not equal plaintext password"
    
    # The hash should be verifiable
    assert verify_password(password, password_hash), "Password should verify against its hash"
    
    # A different password should not verify
    if len(password) > 0:
        different_password = password + "x"
        assert not verify_password(different_password, password_hash), \
            "Different password should not verify against hash"
