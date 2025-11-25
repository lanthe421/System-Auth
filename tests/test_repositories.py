"""Property-based tests for repository operations."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.models.base import Base
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.models.permission import Permission
from app.models.role import Role


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
def valid_permission_data(draw):
    """Generate valid permission data."""
    resources = ['documents', 'projects', 'reports', 'users', 'settings']
    actions = ['create', 'read', 'update', 'delete']
    
    resource = draw(st.sampled_from(resources))
    action = draw(st.sampled_from(actions))
    description = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
    ))
    
    return {
        "resource": resource,
        "action": action,
        "description": description
    }


@st.composite
def valid_role_data(draw):
    """Generate valid role data."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-')))
    description = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=('Cs', 'Cc')))
    ))
    
    return {
        "name": name,
        "description": description
    }


# Feature: auth-system, Property 18: Permission definition storage
# Validates: Requirements 7.1
@given(permission_data=valid_permission_data())
@settings(max_examples=100, deadline=None)
def test_property_18_permission_definition_storage(permission_data):
    """
    Property 18: Permission definition storage
    
    For any valid permission definition (resource + action), creating the
    permission should store it in the database with a unique identifier.
    
    Validates: Requirements 7.1
    """
    db_session, test_engine = get_test_db()
    
    try:
        repo = PermissionRepository(db_session)
        
        # Create the permission
        permission = repo.create(permission_data)
        
        # Verify permission was stored with a unique ID
        assert permission.id is not None, "Permission should have a unique ID"
        assert permission.id > 0, "Permission ID should be positive"
        
        # Verify all fields are stored correctly
        assert permission.resource == permission_data["resource"]
        assert permission.action == permission_data["action"]
        assert permission.description == permission_data["description"]
        
        # Verify permission can be retrieved by ID
        retrieved = repo.get_by_id(permission.id)
        assert retrieved is not None
        assert retrieved.id == permission.id
        assert retrieved.resource == permission_data["resource"]
        assert retrieved.action == permission_data["action"]
        
        # Verify permission can be retrieved by resource and action
        retrieved_by_resource_action = repo.get_by_resource_action(
            permission_data["resource"],
            permission_data["action"]
        )
        assert retrieved_by_resource_action is not None
        assert retrieved_by_resource_action.id == permission.id
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)


# Feature: auth-system, Property 14: Role creation with permissions
# Validates: Requirements 6.1, 9.2
@given(role_data=valid_role_data(), num_permissions=st.integers(min_value=1, max_value=5))
@settings(max_examples=100, deadline=None)
def test_property_14_role_creation_with_permissions(role_data, num_permissions):
    """
    Property 14: Role creation with permissions
    
    For any valid role definition with a set of permissions, creating the role
    should store both the role and its permission associations in the database.
    
    Validates: Requirements 6.1, 9.2
    """
    db_session, test_engine = get_test_db()
    
    try:
        perm_repo = PermissionRepository(db_session)
        role_repo = RoleRepository(db_session)
        
        # Create permissions first
        permissions = []
        resources = ['documents', 'projects', 'reports', 'users', 'settings']
        actions = ['create', 'read', 'update', 'delete']
        
        for i in range(num_permissions):
            perm_data = {
                "resource": resources[i % len(resources)],
                "action": actions[i % len(actions)],
                "description": f"Permission {i}"
            }
            perm = perm_repo.create(perm_data)
            permissions.append(perm)
        
        permission_ids = [p.id for p in permissions]
        
        # Create role with permissions
        role = role_repo.create(role_data, permission_ids=permission_ids)
        
        # Verify role was stored with a unique ID
        assert role.id is not None, "Role should have a unique ID"
        assert role.id > 0, "Role ID should be positive"
        
        # Verify role fields are stored correctly
        assert role.name == role_data["name"]
        assert role.description == role_data["description"]
        
        # Verify role has the correct permissions associated
        db_session.refresh(role)
        assert len(role.permissions) == num_permissions, f"Role should have {num_permissions} permissions"
        
        role_permission_ids = {p.id for p in role.permissions}
        expected_permission_ids = set(permission_ids)
        assert role_permission_ids == expected_permission_ids, "Role should have all specified permissions"
        
        # Verify role can be retrieved by ID
        retrieved = role_repo.get_by_id(role.id)
        assert retrieved is not None
        assert retrieved.id == role.id
        assert retrieved.name == role_data["name"]
        assert len(retrieved.permissions) == num_permissions
        
        # Verify role can be retrieved by name
        retrieved_by_name = role_repo.get_by_name(role_data["name"])
        assert retrieved_by_name is not None
        assert retrieved_by_name.id == role.id
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)
