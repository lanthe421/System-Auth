"""Property-based tests for authorization service operations."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.models.base import Base
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
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
    
    return session, test_engine


# Hypothesis strategies for generating test data
@st.composite
def resource_action_pair(draw):
    """Generate a resource and action pair."""
    resource = draw(st.sampled_from(['documents', 'projects', 'reports', 'users', 'settings']))
    action = draw(st.sampled_from(['read', 'create', 'update', 'delete']))
    return resource, action


@st.composite
def user_with_role_strategy(draw):
    """Generate a user with a role that has permissions."""
    # Generate user data
    first_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    last_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))))
    email = f"user{draw(st.integers(min_value=1, max_value=100000))}@example.com"
    
    # Generate role data
    role_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-')))
    
    # Generate unique permissions (use a set to ensure uniqueness)
    num_permissions = draw(st.integers(min_value=1, max_value=5))
    permissions = []
    seen = set()
    for _ in range(num_permissions):
        perm = draw(resource_action_pair())
        if perm not in seen:
            permissions.append(perm)
            seen.add(perm)
    
    # Ensure at least one permission
    if not permissions:
        permissions = [draw(resource_action_pair())]
    
    return {
        "user": {"first_name": first_name, "last_name": last_name, "email": email},
        "role": {"name": role_name},
        "permissions": permissions
    }


# Feature: auth-system, Property 15: Role assignment grants permissions
# Validates: Requirements 6.2
@given(test_data=user_with_role_strategy())
@settings(max_examples=100, deadline=None)
def test_property_15_role_assignment_grants_permissions(test_data):
    """
    Property 15: Role assignment grants permissions
    
    For any user assigned a role, the user should gain access to all resources
    covered by that role's permissions.
    
    Validates: Requirements 6.2
    """
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        role_service = RoleService(db_session)
        
        # Create permissions
        permission_ids = []
        for resource, action in test_data["permissions"]:
            perm = Permission(resource=resource, action=action)
            db_session.add(perm)
            db_session.commit()
            db_session.refresh(perm)
            permission_ids.append(perm.id)
        
        # Create role with permissions
        role = role_service.create_role(
            name=test_data["role"]["name"],
            permission_ids=permission_ids
        )
        
        # Create user
        user = User(
            first_name=test_data["user"]["first_name"],
            last_name=test_data["user"]["last_name"],
            email=test_data["user"]["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Assign role to user
        success = role_service.assign_role(user.id, role.id)
        assert success is True
        
        # Verify user has access to all permissions from the role
        for resource, action in test_data["permissions"]:
            has_permission = permission_service.check_permission(user.id, resource, action)
            assert has_permission is True, f"User should have {action} permission on {resource} after role assignment"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 16: Role revocation removes permissions
# Validates: Requirements 6.3
@given(test_data=user_with_role_strategy())
@settings(max_examples=100, deadline=None)
def test_property_16_role_revocation_removes_permissions(test_data):
    """
    Property 16: Role revocation removes permissions
    
    For any user having a role revoked, the user should lose access to resources
    granted only by that role (but retain access from other sources).
    
    Validates: Requirements 6.3
    """
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        role_service = RoleService(db_session)
        
        # Create permissions
        permission_ids = []
        for resource, action in test_data["permissions"]:
            perm = Permission(resource=resource, action=action)
            db_session.add(perm)
            db_session.commit()
            db_session.refresh(perm)
            permission_ids.append(perm.id)
        
        # Create role with permissions
        role = role_service.create_role(
            name=test_data["role"]["name"],
            permission_ids=permission_ids
        )
        
        # Create user
        user = User(
            first_name=test_data["user"]["first_name"],
            last_name=test_data["user"]["last_name"],
            email=test_data["user"]["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Assign role to user
        role_service.assign_role(user.id, role.id)
        
        # Verify user has permissions
        for resource, action in test_data["permissions"]:
            has_permission = permission_service.check_permission(user.id, resource, action)
            assert has_permission is True
        
        # Revoke role from user
        success = role_service.revoke_role(user.id, role.id)
        assert success is True
        
        # Verify user no longer has permissions from that role
        for resource, action in test_data["permissions"]:
            has_permission = permission_service.check_permission(user.id, resource, action)
            assert has_permission is False, f"User should not have {action} permission on {resource} after role revocation"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 17: Role update propagation
# Validates: Requirements 6.4, 9.3
@given(
    initial_data=user_with_role_strategy(),
    new_permissions=st.lists(resource_action_pair(), min_size=1, max_size=5, unique=True)
)
@settings(max_examples=100, deadline=None)
def test_property_17_role_update_propagation(initial_data, new_permissions):
    """
    Property 17: Role update propagation
    
    For any role with assigned users, updating the role's permissions should
    immediately affect the access rights of all users with that role.
    
    Validates: Requirements 6.4, 9.3
    """
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        role_service = RoleService(db_session)
        
        # Create initial permissions
        initial_permission_ids = []
        for resource, action in initial_data["permissions"]:
            perm = Permission(resource=resource, action=action)
            db_session.add(perm)
            db_session.commit()
            db_session.refresh(perm)
            initial_permission_ids.append(perm.id)
        
        # Create role with initial permissions
        role = role_service.create_role(
            name=initial_data["role"]["name"],
            permission_ids=initial_permission_ids
        )
        
        # Create user
        user = User(
            first_name=initial_data["user"]["first_name"],
            last_name=initial_data["user"]["last_name"],
            email=initial_data["user"]["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Assign role to user
        role_service.assign_role(user.id, role.id)
        
        # Verify user has initial permissions
        for resource, action in initial_data["permissions"]:
            has_permission = permission_service.check_permission(user.id, resource, action)
            assert has_permission is True
        
        # Create new permissions
        new_permission_ids = []
        for resource, action in new_permissions:
            # Check if permission already exists
            existing_perm = db_session.query(Permission).filter(
                Permission.resource == resource,
                Permission.action == action
            ).first()
            
            if existing_perm:
                new_permission_ids.append(existing_perm.id)
            else:
                perm = Permission(resource=resource, action=action)
                db_session.add(perm)
                db_session.commit()
                db_session.refresh(perm)
                new_permission_ids.append(perm.id)
        
        # Update role permissions
        updated_role = role_service.update_role_permissions(role.id, new_permission_ids)
        assert updated_role is not None
        
        # Verify user now has new permissions
        for resource, action in new_permissions:
            has_permission = permission_service.check_permission(user.id, resource, action)
            assert has_permission is True, f"User should have {action} permission on {resource} after role update"
        
        # Verify user no longer has old permissions (unless they're in the new set)
        new_perms_set = set(new_permissions)
        for resource, action in initial_data["permissions"]:
            if (resource, action) not in new_perms_set:
                has_permission = permission_service.check_permission(user.id, resource, action)
                assert has_permission is False, f"User should not have {action} permission on {resource} after role update removed it"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 19: Direct permission grant
# Validates: Requirements 7.2
@given(
    user_data=st.fixed_dictionaries({
        "first_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "last_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "email": st.emails()
    }),
    perm=resource_action_pair()
)
@settings(max_examples=100, deadline=None)
def test_property_19_direct_permission_grant(user_data, perm):
    """
    Property 19: Direct permission grant
    
    For any user granted a direct permission, the user should gain access to
    that specific resource-action combination.
    
    Validates: Requirements 7.2
    """
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        
        resource, action = perm
        
        # Create permission
        permission = Permission(resource=resource, action=action)
        db_session.add(permission)
        db_session.commit()
        db_session.refresh(permission)
        
        # Create user
        user = User(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verify user doesn't have permission initially
        has_permission_before = permission_service.check_permission(user.id, resource, action)
        assert has_permission_before is False
        
        # Grant direct permission to user
        success = permission_service.grant_permission(user.id, resource, action)
        assert success is True
        
        # Verify user now has the permission
        has_permission_after = permission_service.check_permission(user.id, resource, action)
        assert has_permission_after is True, f"User should have {action} permission on {resource} after direct grant"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 20: Direct permission revocation
# Validates: Requirements 7.3
@given(
    user_data=st.fixed_dictionaries({
        "first_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "last_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "email": st.emails()
    }),
    perm=resource_action_pair()
)
@settings(max_examples=100, deadline=None)
def test_property_20_direct_permission_revocation(user_data, perm):
    """
    Property 20: Direct permission revocation
    
    For any user having a direct permission revoked, the user should lose access
    to that specific resource-action combination (unless granted through a role).
    
    Validates: Requirements 7.3
    """
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        
        resource, action = perm
        
        # Create permission
        permission = Permission(resource=resource, action=action)
        db_session.add(permission)
        db_session.commit()
        db_session.refresh(permission)
        
        # Create user
        user = User(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Grant direct permission to user
        permission_service.grant_permission(user.id, resource, action)
        
        # Verify user has the permission
        has_permission_before = permission_service.check_permission(user.id, resource, action)
        assert has_permission_before is True
        
        # Revoke direct permission from user
        success = permission_service.revoke_permission(user.id, resource, action)
        assert success is True
        
        # Verify user no longer has the permission
        has_permission_after = permission_service.check_permission(user.id, resource, action)
        assert has_permission_after is False, f"User should not have {action} permission on {resource} after direct revocation"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 21: Authorization check correctness
# Validates: Requirements 8.1, 8.2
@given(
    user_data=st.fixed_dictionaries({
        "first_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "last_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "email": st.emails()
    }),
    granted_perm=resource_action_pair(),
    denied_perm=resource_action_pair()
)
@settings(max_examples=100, deadline=None)
def test_property_21_authorization_check_correctness(user_data, granted_perm, denied_perm):
    """
    Property 21: Authorization check correctness
    
    For any authenticated user and resource request, the system should return
    the resource if the user has permission (via role or direct grant) and
    return 403 if they do not.
    
    Validates: Requirements 8.1, 8.2
    """
    # Ensure granted and denied permissions are different
    assume(granted_perm != denied_perm)
    
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        
        granted_resource, granted_action = granted_perm
        denied_resource, denied_action = denied_perm
        
        # Create permissions
        granted_permission = Permission(resource=granted_resource, action=granted_action)
        db_session.add(granted_permission)
        
        denied_permission = Permission(resource=denied_resource, action=denied_action)
        db_session.add(denied_permission)
        
        db_session.commit()
        db_session.refresh(granted_permission)
        db_session.refresh(denied_permission)
        
        # Create user
        user = User(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Grant only the granted permission to user
        permission_service.grant_permission(user.id, granted_resource, granted_action)
        
        # Verify user has access to granted permission
        has_granted = permission_service.check_permission(user.id, granted_resource, granted_action)
        assert has_granted is True, f"User should have {granted_action} permission on {granted_resource}"
        
        # Verify user does NOT have access to denied permission
        has_denied = permission_service.check_permission(user.id, denied_resource, denied_action)
        assert has_denied is False, f"User should not have {denied_action} permission on {denied_resource}"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 22: Permission source union
# Validates: Requirements 8.4, 8.5
@given(
    user_data=st.fixed_dictionaries({
        "first_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "last_name": st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        "email": st.emails()
    }),
    perm=resource_action_pair()
)
@settings(max_examples=100, deadline=None)
def test_property_22_permission_source_union(user_data, perm):
    """
    Property 22: Permission source union
    
    For any user with the same permission granted through multiple sources
    (role and direct grant), the user should have access regardless of which
    source is checked.
    
    Validates: Requirements 8.4, 8.5
    """
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        role_service = RoleService(db_session)
        
        resource, action = perm
        
        # Create permission
        permission = Permission(resource=resource, action=action)
        db_session.add(permission)
        db_session.commit()
        db_session.refresh(permission)
        
        # Create role with the permission
        role = role_service.create_role(
            name="test_role",
            permission_ids=[permission.id]
        )
        
        # Create user
        user = User(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Grant permission through role
        role_service.assign_role(user.id, role.id)
        
        # Verify user has permission from role
        has_permission_from_role = permission_service.check_permission(user.id, resource, action)
        assert has_permission_from_role is True
        
        # Also grant the same permission directly
        permission_service.grant_permission(user.id, resource, action)
        
        # Verify user still has permission (from both sources)
        has_permission_from_both = permission_service.check_permission(user.id, resource, action)
        assert has_permission_from_both is True
        
        # Revoke the role
        role_service.revoke_role(user.id, role.id)
        
        # Verify user still has permission (from direct grant)
        has_permission_from_direct = permission_service.check_permission(user.id, resource, action)
        assert has_permission_from_direct is True, "User should still have permission from direct grant after role revocation"
        
        # Revoke direct permission
        permission_service.revoke_permission(user.id, resource, action)
        
        # Verify user no longer has permission
        has_permission_after_all_revoked = permission_service.check_permission(user.id, resource, action)
        assert has_permission_after_all_revoked is False, "User should not have permission after all sources revoked"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)



# Feature: auth-system, Property 23: Role deletion cleanup
# Validates: Requirements 9.4
@given(test_data=user_with_role_strategy())
@settings(max_examples=100, deadline=None)
def test_property_23_role_deletion_cleanup(test_data):
    """
    Property 23: Role deletion cleanup
    
    For any role being deleted, all user-role associations should be removed
    and affected users should lose permissions granted only by that role.
    
    Validates: Requirements 9.4
    """
    db_session, test_engine = get_test_db()
    
    try:
        permission_service = PermissionService(db_session)
        role_service = RoleService(db_session)
        
        # Create permissions
        permission_ids = []
        for resource, action in test_data["permissions"]:
            perm = Permission(resource=resource, action=action)
            db_session.add(perm)
            db_session.commit()
            db_session.refresh(perm)
            permission_ids.append(perm.id)
        
        # Create role with permissions
        role = role_service.create_role(
            name=test_data["role"]["name"],
            permission_ids=permission_ids
        )
        
        # Create user
        user = User(
            first_name=test_data["user"]["first_name"],
            last_name=test_data["user"]["last_name"],
            email=test_data["user"]["email"],
            password_hash="dummy_hash",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Assign role to user
        role_service.assign_role(user.id, role.id)
        
        # Verify user has permissions from the role
        for resource, action in test_data["permissions"]:
            has_permission = permission_service.check_permission(user.id, resource, action)
            assert has_permission is True
        
        # Delete the role
        success = role_service.delete_role(role.id)
        assert success is True
        
        # Verify role is deleted
        deleted_role = role_service.get_role(role.id)
        assert deleted_role is None, "Role should be deleted"
        
        # Verify user no longer has permissions from the deleted role
        for resource, action in test_data["permissions"]:
            has_permission = permission_service.check_permission(user.id, resource, action)
            assert has_permission is False, f"User should not have {action} permission on {resource} after role deletion"
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)
