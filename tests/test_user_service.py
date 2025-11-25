"""Property-based tests for user service operations."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.models.base import Base
from app.services.user_service import UserService
from app.models.user import User


def get_test_db():
    """Create a fresh database session for testing."""
    # Create in-memory SQLite database for testing
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
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


# Feature: auth-system, Property 1: Valid registration creates active account
# Validates: Requirements 1.1
@given(user_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_1_valid_registration_creates_active_account(user_data):
    """
    Property 1: Valid registration creates active account
    
    For any valid user registration data (with matching passwords and unique email),
    creating a new account should result in a user record with is_active=True and
    all provided fields correctly stored.
    
    Validates: Requirements 1.1
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = UserService(db_session)
        
        # Register the user
        user = service.register_user(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]  # Matching password
        )
        
        # Verify user was created with is_active=True
        assert user is not None, "User should be created"
        assert user.is_active is True, "User should be active"
        
        # Verify all fields are correctly stored
        assert user.first_name == user_data["first_name"]
        assert user.last_name == user_data["last_name"]
        assert user.middle_name == user_data["middle_name"]
        assert user.email == user_data["email"]
        
        # Verify password is hashed (not stored as plaintext)
        assert user.password_hash != user_data["password"]
        
        # Verify user has an ID (was persisted to database)
        assert user.id is not None
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 2: Duplicate email rejection
# Validates: Requirements 1.2
@given(user_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_2_duplicate_email_rejection(user_data):
    """
    Property 2: Duplicate email rejection
    
    For any existing user email, attempting to register a new account with that
    email should be rejected with an appropriate error.
    
    Validates: Requirements 1.2
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = UserService(db_session)
        
        # Register the first user
        user1 = service.register_user(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]
        )
        
        assert user1 is not None
        
        # Attempt to register a second user with the same email
        with pytest.raises(ValueError, match="Email already exists"):
            service.register_user(
                first_name="Different",
                last_name="User",
                middle_name=None,
                email=user_data["email"],  # Same email
                password="different_password",
                password_confirm="different_password"
            )
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 3: Password mismatch rejection
# Validates: Requirements 1.3
@given(user_data=valid_user_data(), different_password=st.text(min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_property_3_password_mismatch_rejection(user_data, different_password):
    """
    Property 3: Password mismatch rejection
    
    For any registration data where password and password_confirm do not match,
    the registration should be rejected with a validation error.
    
    Validates: Requirements 1.3
    """
    # Ensure passwords are different
    assume(user_data["password"] != different_password)
    
    db_session, test_engine = get_test_db()
    
    try:
        service = UserService(db_session)
        
        # Attempt to register with mismatched passwords
        with pytest.raises(ValueError, match="Passwords do not match"):
            service.register_user(
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                middle_name=user_data["middle_name"],
                email=user_data["email"],
                password=user_data["password"],
                password_confirm=different_password  # Different password
            )
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 10: Profile update persistence
# Validates: Requirements 4.1
@given(
    initial_data=valid_user_data(),
    update_first_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
    update_last_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
)
@settings(max_examples=100, deadline=None)
def test_property_10_profile_update_persistence(initial_data, update_first_name, update_last_name):
    """
    Property 10: Profile update persistence
    
    For any authenticated user submitting valid profile updates, the changes
    should be persisted to the database and reflected in subsequent queries.
    
    Validates: Requirements 4.1
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = UserService(db_session)
        
        # Create initial user
        user = service.register_user(
            first_name=initial_data["first_name"],
            last_name=initial_data["last_name"],
            middle_name=initial_data["middle_name"],
            email=initial_data["email"],
            password=initial_data["password"],
            password_confirm=initial_data["password"]
        )
        
        user_id = user.id
        
        # Update the user's profile
        updated_user = service.update_profile(
            user_id=user_id,
            first_name=update_first_name,
            last_name=update_last_name
        )
        
        assert updated_user is not None
        assert updated_user.first_name == update_first_name
        assert updated_user.last_name == update_last_name
        
        # Verify persistence by querying again
        retrieved_user = service.get_user(user_id)
        assert retrieved_user is not None
        assert retrieved_user.first_name == update_first_name
        assert retrieved_user.last_name == update_last_name
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 11: Email uniqueness on update
# Validates: Requirements 4.2
@given(user1_data=valid_user_data(), user2_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_11_email_uniqueness_on_update(user1_data, user2_data):
    """
    Property 11: Email uniqueness on update
    
    For any user attempting to update their email to one already in use by
    another user, the update should be rejected with an error.
    
    Validates: Requirements 4.2
    """
    # Ensure emails are different
    assume(user1_data["email"] != user2_data["email"])
    
    db_session, test_engine = get_test_db()
    
    try:
        service = UserService(db_session)
        
        # Create two users with different emails
        user1 = service.register_user(
            first_name=user1_data["first_name"],
            last_name=user1_data["last_name"],
            middle_name=user1_data["middle_name"],
            email=user1_data["email"],
            password=user1_data["password"],
            password_confirm=user1_data["password"]
        )
        
        user2 = service.register_user(
            first_name=user2_data["first_name"],
            last_name=user2_data["last_name"],
            middle_name=user2_data["middle_name"],
            email=user2_data["email"],
            password=user2_data["password"],
            password_confirm=user2_data["password"]
        )
        
        # Attempt to update user2's email to user1's email
        with pytest.raises(ValueError, match="Email already exists"):
            service.update_profile(
                user_id=user2.id,
                email=user1.email  # Try to use user1's email
            )
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 12: Soft delete sets inactive
# Validates: Requirements 5.1, 5.4
@given(user_data=valid_user_data())
@settings(max_examples=100, deadline=None)
def test_property_12_soft_delete_sets_inactive(user_data):
    """
    Property 12: Soft delete sets inactive
    
    For any user requesting account deletion, the user's is_active field should
    be set to False and all other data should remain unchanged in the database.
    
    Validates: Requirements 5.1, 5.4
    """
    db_session, test_engine = get_test_db()
    
    try:
        service = UserService(db_session)
        
        # Create a user
        user = service.register_user(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            middle_name=user_data["middle_name"],
            email=user_data["email"],
            password=user_data["password"],
            password_confirm=user_data["password"]
        )
        
        user_id = user.id
        original_first_name = user.first_name
        original_last_name = user.last_name
        original_email = user.email
        
        # Soft delete the user
        deleted = service.delete_account(user_id)
        assert deleted is True
        
        # Verify user still exists but is inactive
        deleted_user = service.get_user(user_id)
        assert deleted_user is not None
        assert deleted_user.is_active is False
        
        # Verify all other data remains unchanged
        assert deleted_user.first_name == original_first_name
        assert deleted_user.last_name == original_last_name
        assert deleted_user.email == original_email
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)
