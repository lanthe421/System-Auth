"""Tests for database seed script."""

import pytest
from sqlalchemy.orm import Session
from app.models import User, Role, Permission
from app.utils.password import verify_password


def test_seed_creates_permissions(db_session: Session):
    """Test that seed script creates all required permissions."""
    # Import seed functions
    from seed import create_permissions
    
    # Create permissions
    permissions = create_permissions(db_session)
    
    # Verify we have 12 permissions (3 resources × 4 actions)
    assert len(permissions) == 12
    
    # Verify all resource-action combinations exist
    resources = ["documents", "projects", "reports"]
    actions = ["read", "create", "update", "delete"]
    
    for resource in resources:
        for action in actions:
            key = f"{resource}:{action}"
            assert key in permissions
            assert permissions[key].resource == resource
            assert permissions[key].action == action
    
    # Verify permissions are in database
    db_permissions = db_session.query(Permission).all()
    assert len(db_permissions) == 12


def test_seed_creates_admin_role(db_session: Session):
    """Test that seed script creates admin role with all permissions."""
    from seed import create_permissions, create_admin_role
    
    # Create permissions first
    permissions = create_permissions(db_session)
    
    # Create admin role
    admin_role = create_admin_role(db_session, permissions)
    
    # Verify admin role exists
    assert admin_role is not None
    assert admin_role.name == "admin"
    assert admin_role.description == "Administrator role with full system access"
    
    # Verify admin role has all permissions
    assert len(admin_role.permissions) == 12
    
    # Verify role is in database
    db_role = db_session.query(Role).filter_by(name="admin").first()
    assert db_role is not None
    assert len(db_role.permissions) == 12


def test_seed_creates_user_role(db_session: Session):
    """Test that seed script creates user role with read permissions only."""
    from seed import create_permissions, create_user_role
    
    # Create permissions first
    permissions = create_permissions(db_session)
    
    # Create user role
    user_role = create_user_role(db_session, permissions)
    
    # Verify user role exists
    assert user_role is not None
    assert user_role.name == "user"
    assert user_role.description == "Default user role with read-only access"
    
    # Verify user role has only read permissions (3 resources)
    assert len(user_role.permissions) == 3
    
    # Verify all permissions are read permissions
    for perm in user_role.permissions:
        assert perm.action == "read"
    
    # Verify role is in database
    db_role = db_session.query(Role).filter_by(name="user").first()
    assert db_role is not None
    assert len(db_role.permissions) == 3


def test_seed_creates_admin_user(db_session: Session):
    """Test that seed script creates admin user with admin role."""
    from seed import create_permissions, create_admin_role, create_admin_user
    
    # Create permissions and admin role first
    permissions = create_permissions(db_session)
    admin_role = create_admin_role(db_session, permissions)
    
    # Create admin user
    admin_user = create_admin_user(db_session, admin_role)
    
    # Verify admin user exists
    assert admin_user is not None
    assert admin_user.email == "admin@example.com"
    assert admin_user.first_name == "System"
    assert admin_user.last_name == "Administrator"
    assert admin_user.is_active is True
    
    # Verify password is hashed correctly
    assert verify_password("admin123", admin_user.password_hash)
    
    # Verify admin user has admin role
    assert len(admin_user.roles) == 1
    assert admin_user.roles[0].name == "admin"
    
    # Verify user is in database
    db_user = db_session.query(User).filter_by(email="admin@example.com").first()
    assert db_user is not None
    assert len(db_user.roles) == 1


def test_seed_idempotent_permissions(db_session: Session):
    """Test that running seed script multiple times doesn't create duplicates."""
    from seed import create_permissions
    
    # Create permissions first time
    permissions1 = create_permissions(db_session)
    assert len(permissions1) == 12
    
    # Create permissions second time
    permissions2 = create_permissions(db_session)
    assert len(permissions2) == 12
    
    # Verify no duplicates in database
    db_permissions = db_session.query(Permission).all()
    assert len(db_permissions) == 12


def test_seed_idempotent_roles(db_session: Session):
    """Test that running seed script multiple times doesn't create duplicate roles."""
    from seed import create_permissions, create_admin_role, create_user_role
    
    # Create permissions
    permissions = create_permissions(db_session)
    
    # Create roles first time
    admin_role1 = create_admin_role(db_session, permissions)
    user_role1 = create_user_role(db_session, permissions)
    
    # Create roles second time
    admin_role2 = create_admin_role(db_session, permissions)
    user_role2 = create_user_role(db_session, permissions)
    
    # Verify same roles returned
    assert admin_role1.id == admin_role2.id
    assert user_role1.id == user_role2.id
    
    # Verify no duplicates in database
    db_roles = db_session.query(Role).all()
    assert len(db_roles) == 2


def test_seed_idempotent_users(db_session: Session):
    """Test that running seed script multiple times doesn't create duplicate users."""
    from seed import create_permissions, create_admin_role, create_admin_user
    
    # Create permissions and admin role
    permissions = create_permissions(db_session)
    admin_role = create_admin_role(db_session, permissions)
    
    # Create admin user first time
    admin_user1 = create_admin_user(db_session, admin_role)
    
    # Create admin user second time
    admin_user2 = create_admin_user(db_session, admin_role)
    
    # Verify same user returned
    assert admin_user1.id == admin_user2.id
    
    # Verify no duplicates in database
    db_users = db_session.query(User).all()
    assert len(db_users) == 1


def test_seed_full_workflow(db_session: Session):
    """Test complete seed workflow."""
    from seed import create_permissions, create_admin_role, create_user_role, create_admin_user
    
    # Run complete seed workflow
    permissions = create_permissions(db_session)
    admin_role = create_admin_role(db_session, permissions)
    user_role = create_user_role(db_session, permissions)
    admin_user = create_admin_user(db_session, admin_role)
    
    # Verify final state
    assert db_session.query(Permission).count() == 12
    assert db_session.query(Role).count() == 2
    assert db_session.query(User).count() == 1
    
    # Verify admin user has access to all permissions through admin role
    admin_from_db = db_session.query(User).filter_by(email="admin@example.com").first()
    assert admin_from_db is not None
    
    # Get all permissions through roles
    all_permissions = set()
    for role in admin_from_db.roles:
        for perm in role.permissions:
            all_permissions.add(f"{perm.resource}:{perm.action}")
    
    assert len(all_permissions) == 12
