"""Tests for error handling and validation.

Requirements: 1.2, 1.3, 2.2, 2.3, 4.2, 8.2, 8.3, 9.5
"""

import pytest
from pydantic import ValidationError

from app.api.schemas import (
    UserRegistration,
    UserLogin,
    UserUpdate,
    PermissionCreate,
    RoleCreate,
    RoleUpdate
)


def test_validation_error_password_mismatch():
    """
    Test that password mismatch raises validation error.
    
    Requirements: 1.3
    """
    with pytest.raises(ValidationError) as exc_info:
        UserRegistration(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="password123",
            password_confirm="different123"
        )
    
    errors = exc_info.value.errors()
    assert any("match" in str(error).lower() for error in errors)


def test_validation_error_weak_password_too_short():
    """
    Test that weak password (too short) raises validation error.
    
    Requirements: 1.4
    """
    with pytest.raises(ValidationError) as exc_info:
        UserRegistration(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="short",
            password_confirm="short"
        )
    
    errors = exc_info.value.errors()
    assert any("8 characters" in str(error).lower() for error in errors)


def test_validation_error_weak_password_no_number():
    """
    Test that password without number raises validation error.
    
    Requirements: 1.4
    """
    with pytest.raises(ValidationError) as exc_info:
        UserRegistration(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="passwordonly",
            password_confirm="passwordonly"
        )
    
    errors = exc_info.value.errors()
    assert any("number" in str(error).lower() for error in errors)


def test_validation_error_weak_password_no_letter():
    """
    Test that password without letter raises validation error.
    
    Requirements: 1.4
    """
    with pytest.raises(ValidationError) as exc_info:
        UserRegistration(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="12345678",
            password_confirm="12345678"
        )
    
    errors = exc_info.value.errors()
    assert any("letter" in str(error).lower() for error in errors)


def test_validation_error_invalid_email():
    """
    Test that invalid email format raises validation error.
    
    Requirements: 1.2
    """
    with pytest.raises(ValidationError):
        UserRegistration(
            first_name="John",
            last_name="Doe",
            email="not-an-email",
            password="password123",
            password_confirm="password123"
        )


def test_validation_error_empty_name():
    """
    Test that empty name fields raise validation error.
    
    Requirements: 1.2
    """
    with pytest.raises(ValidationError) as exc_info:
        UserRegistration(
            first_name="   ",
            last_name="Doe",
            email="john@example.com",
            password="password123",
            password_confirm="password123"
        )
    
    errors = exc_info.value.errors()
    assert any("whitespace" in str(error).lower() for error in errors)


def test_validation_error_empty_password():
    """
    Test that empty password raises validation error.
    
    Requirements: 2.1
    """
    with pytest.raises(ValidationError):
        UserLogin(
            email="john@example.com",
            password="   "
        )


def test_validation_error_invalid_permission_action():
    """
    Test that invalid permission action raises validation error.
    
    Requirements: 7.1
    """
    with pytest.raises(ValidationError) as exc_info:
        PermissionCreate(
            resource="documents",
            action="invalid_action",
            description="Test permission"
        )
    
    errors = exc_info.value.errors()
    assert any("create" in str(error).lower() or "read" in str(error).lower() for error in errors)


def test_validation_error_empty_permission_resource():
    """
    Test that empty permission resource raises validation error.
    
    Requirements: 7.1
    """
    with pytest.raises(ValidationError) as exc_info:
        PermissionCreate(
            resource="   ",
            action="read",
            description="Test permission"
        )
    
    errors = exc_info.value.errors()
    assert any("whitespace" in str(error).lower() for error in errors)


def test_validation_error_negative_permission_id():
    """
    Test that negative permission ID raises validation error.
    
    Requirements: 9.2
    """
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="test_role",
            description="Test role",
            permission_ids=[-1, 0]
        )
    
    errors = exc_info.value.errors()
    assert any("positive" in str(error).lower() for error in errors)


def test_validation_error_empty_role_name():
    """
    Test that empty role name raises validation error.
    
    Requirements: 6.1
    """
    with pytest.raises(ValidationError) as exc_info:
        RoleCreate(
            name="   ",
            description="Test role",
            permission_ids=[]
        )
    
    errors = exc_info.value.errors()
    assert any("whitespace" in str(error).lower() for error in errors)


def test_user_update_validation():
    """
    Test that UserUpdate validates fields correctly.
    
    Requirements: 4.1, 4.3
    """
    # Valid update should work
    update = UserUpdate(
        first_name="John",
        email="john@example.com"
    )
    assert update.first_name == "John"
    assert update.email == "john@example.com"
    
    # Empty name should fail
    with pytest.raises(ValidationError):
        UserUpdate(first_name="   ")
    
    # Weak password should fail
    with pytest.raises(ValidationError):
        UserUpdate(password="short")


def test_role_update_validation():
    """
    Test that RoleUpdate validates permission IDs correctly.
    
    Requirements: 6.4, 9.3
    """
    # Valid update should work
    update = RoleUpdate(permission_ids=[1, 2, 3])
    assert update.permission_ids == [1, 2, 3]
    
    # Negative IDs should fail
    with pytest.raises(ValidationError):
        RoleUpdate(permission_ids=[-1, 2])
    
    # Zero should fail
    with pytest.raises(ValidationError):
        RoleUpdate(permission_ids=[0, 2])
