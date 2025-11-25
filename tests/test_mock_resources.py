"""Property-based tests for mock resource authorization."""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings as hypothesis_settings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User
from app.models.permission import Permission
from app.main import app
from app.database import get_db
from app.utils.jwt import generate_access_token
from app.repositories.session_repository import SessionRepository
from app.config import settings


def get_test_db():
    """Create a fresh database session for testing."""
    # Create in-memory SQLite database for testing
    # Use check_same_thread=False to allow usage across threads (needed for TestClient)
    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
    return session, test_engine


# Hypothesis strategies for generating test data
@st.composite
def resource_type_strategy(draw):
    """Generate a resource type (documents, projects, or reports)."""
    return draw(st.sampled_from(['documents', 'projects', 'reports']))


@st.composite
def user_with_permission_strategy(draw):
    """Generate a user with a specific permission."""
    # Generate user data
    first_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    last_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    email = f"user{draw(st.integers(min_value=1, max_value=100000))}@example.com"
    
    # Generate resource type
    resource = draw(resource_type_strategy())
    
    return {
        "user": {"first_name": first_name, "last_name": last_name, "email": email},
        "resource": resource
    }


# Feature: auth-system, Property 24: Mock resource authorization
# Validates: Requirements 10.2, 10.3
@given(test_data=user_with_permission_strategy())
@hypothesis_settings(max_examples=100, deadline=None)
def test_property_24_mock_resource_authorization(test_data):
    """
    Property 24: Mock resource authorization
    
    For any mock resource endpoint, the same authorization rules should apply
    as for real resources, returning 401 for unauthenticated requests and 403
    for unauthorized requests.
    
    Validates: Requirements 10.2, 10.3
    """
    db_session, test_engine = get_test_db()
    
    try:
        # Override the database dependency
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        
        resource = test_data["resource"]
        endpoint = f"/api/resources/{resource}"
        
        # Test 1: Unauthenticated request should return 401
        response_no_auth = client.get(endpoint)
        assert response_no_auth.status_code == 401, \
            f"Unauthenticated request to {endpoint} should return 401"
        
        # Create user without permission
        user_without_perm = User(
            first_name=test_data["user"]["first_name"],
            last_name=test_data["user"]["last_name"],
            email=test_data["user"]["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user_without_perm)
        db_session.commit()
        db_session.refresh(user_without_perm)
        
        # Create token for user without permission
        token_without_perm = generate_access_token(user_without_perm.id)
        
        # Create session for the token
        session_repo = SessionRepository(db_session)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        session_repo.create_session(user_without_perm.id, token_without_perm, expires_at)
        
        # Test 2: Authenticated user without permission should return 403
        response_no_perm = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {token_without_perm}"}
        )
        assert response_no_perm.status_code == 403, \
            f"Authenticated user without permission should get 403 for {endpoint}"
        
        # Create permission for the resource
        permission = Permission(resource=resource, action="read")
        db_session.add(permission)
        db_session.commit()
        db_session.refresh(permission)
        
        # Create user with permission
        user_with_perm = User(
            first_name=test_data["user"]["first_name"] + "_authorized",
            last_name=test_data["user"]["last_name"],
            email=f"authorized_{test_data['user']['email']}",
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user_with_perm)
        db_session.commit()
        db_session.refresh(user_with_perm)
        
        # Grant permission to user
        user_with_perm.permissions.append(permission)
        db_session.commit()
        
        # Create token for user with permission
        token_with_perm = generate_access_token(user_with_perm.id)
        
        # Create session for the token
        expires_at_2 = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        session_repo.create_session(user_with_perm.id, token_with_perm, expires_at_2)
        
        # Test 3: Authenticated user with permission should return 200
        response_with_perm = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {token_with_perm}"}
        )
        assert response_with_perm.status_code == 200, \
            f"Authenticated user with permission should get 200 for {endpoint}"
        
        # Test 4: Response should contain a list
        data = response_with_perm.json()
        assert isinstance(data, list), \
            f"Response from {endpoint} should be a list"
        
        # Test 5: List should not be empty (we have mock data)
        assert len(data) > 0, \
            f"Response from {endpoint} should contain mock data"
        
    finally:
        app.dependency_overrides.clear()
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)
