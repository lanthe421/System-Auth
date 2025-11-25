"""Property-based tests for authentication service operations."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.models.base import Base
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission


def get_test_db():
    """Create a fresh database session for testing."""
    # Create in-memory SQLite database for testing
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
    # Create default "user" role for testing
    default_role = Role(name="user", description="Default user role")
    session.add(default_role)
    session.commit()
    
    return session, test_engine


# Hypothesis strategies for generating test data
@st.composite
def valid_user_data(draw):
    """Generate valid user registration data."""
    first_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    last_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    middle_name = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
    ))
    
    # Generate a valid email
    local_part = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='._-')))
    domain = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='-')))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu']))
    email = f"{local_part}@{domain}.{tld}"
    
    password = draw(st.text(min_size=1, max_size=50))
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name,
        "email": email,
        "password": password
    }


# Feature: auth-system, Property 5: Default permissions assignment
# Validates: Requirements 1.5
@given(user_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_5_default_permissions_assignment(user_data):
    """
    Property 5: Default permissions assignment
    
    For any newly created user, the user should have at least one role or
    permission assigned after registration completes.
    
    Validates: Requirements 1.5
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = AuthService(db_session)
        
        # Register the user
        user = service.register(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]
        )
        
        # Refresh to get relationships
        db_session.refresh(user)
        
        # Verify user has at least one role assigned
        assert len(user.roles) > 0, "User should have at least one role assigned"
        
        # Verify the default role is "user"
        role_names = [role.name for role in user.roles]
        assert "user" in role_names, "User should have the default 'user' role"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)


# Feature: auth-system, Property 6: Valid login generates token
# Validates: Requirements 2.1, 2.4
@given(user_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_6_valid_login_generates_token(user_data):
    """
    Property 6: Valid login generates token
    
    For any registered active user with correct credentials, login should
    return a valid authentication token that can be used for subsequent requests.
    
    Validates: Requirements 2.1, 2.4
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = AuthService(db_session)
        
        # Register the user
        user = service.register(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]
        )
        
        # Login with correct credentials
        access_token, refresh_token, logged_in_user = service.login(
            email=user_data["email"],
            password=user_data["password"]
        )
        
        # Verify tokens are returned
        assert access_token is not None and len(access_token) > 0
        assert refresh_token is not None and len(refresh_token) > 0
        
        # Verify the correct user is returned
        assert logged_in_user.id == user.id
        assert logged_in_user.email == user_data["email"]
        
        # Verify token can be used to identify the user
        verified_user = service.verify_token_and_get_user(access_token)
        assert verified_user is not None
        assert verified_user.id == user.id
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)


# Feature: auth-system, Property 7: Invalid credentials rejection
# Validates: Requirements 2.2
@given(user_data=valid_user_data(), wrong_password=st.text(min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_property_7_invalid_credentials_rejection(user_data, wrong_password):
    """
    Property 7: Invalid credentials rejection
    
    For any login attempt with incorrect email or password, the system should
    return a 401 error and not create a session.
    
    Validates: Requirements 2.2
    """
    # Ensure wrong password is different from correct password
    assume(user_data["password"] != wrong_password)
    
    db_session, test_engine = get_test_db()
    
    try:
        service = AuthService(db_session)
        
        # Register the user
        user = service.register(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]
        )
        
        # Attempt login with wrong password
        with pytest.raises(ValueError, match="Invalid credentials"):
            service.login(
                email=user_data["email"],
                password=wrong_password
            )
        
        # Attempt login with non-existent email
        with pytest.raises(ValueError, match="Invalid credentials"):
            service.login(
                email="nonexistent@example.com",
                password=user_data["password"]
            )
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)


# Feature: auth-system, Property 9: Logout invalidates token
# Validates: Requirements 3.1, 3.2, 3.3
@given(user_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_9_logout_invalidates_token(user_data):
    """
    Property 9: Logout invalidates token
    
    For any authenticated user, after logout, any subsequent request using the
    same token should be rejected with a 401 error.
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = AuthService(db_session)
        
        # Register and login
        user = service.register(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]
        )
        
        access_token, refresh_token, _ = service.login(
            email=user_data["email"],
            password=user_data["password"]
        )
        
        # Verify token works before logout
        verified_user = service.verify_token_and_get_user(access_token)
        assert verified_user is not None
        assert verified_user.id == user.id
        
        # Logout
        logout_success = service.logout(access_token)
        assert logout_success is True
        
        # Verify token no longer works after logout
        verified_user_after_logout = service.verify_token_and_get_user(access_token)
        assert verified_user_after_logout is None, "Token should be invalid after logout"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)


# Feature: auth-system, Property 13: Deletion triggers logout
# Validates: Requirements 5.2
@given(user_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_13_deletion_triggers_logout(user_data):
    """
    Property 13: Deletion triggers logout
    
    For any authenticated user who deletes their account, their current session
    should be immediately invalidated.
    
    Validates: Requirements 5.2
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = AuthService(db_session)
        
        # Register and login
        user = service.register(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]
        )
        
        user_id = user.id
        
        access_token, refresh_token, _ = service.login(
            email=user_data["email"],
            password=user_data["password"]
        )
        
        # Verify token works before deletion
        verified_user = service.verify_token_and_get_user(access_token)
        assert verified_user is not None
        
        # Delete the account (using UserService since AuthService doesn't have delete)
        from app.services.user_service import UserService
        user_service = UserService(db_session)
        deleted = user_service.delete_account(user_id)
        assert deleted is True
        
        # Verify token no longer works after account deletion
        verified_user_after_deletion = service.verify_token_and_get_user(access_token)
        assert verified_user_after_deletion is None, "Token should be invalid after account deletion"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)
