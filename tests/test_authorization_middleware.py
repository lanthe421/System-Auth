"""Tests for authorization middleware dependencies."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import require_permission, require_admin
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService


async def test_require_permission_with_valid_permission(db_session: Session):
    """Test that require_permission allows access when user has the permission."""
    # Create a user
    user_repo = UserRepository(db_session)
    user = user_repo.create({
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "is_active": True
    })
    
    # Create a permission
    perm_repo = PermissionRepository(db_session)
    permission = perm_repo.create({
        "resource": "documents",
        "action": "read"
    })
    
    # Grant permission to user
    perm_service = PermissionService(db_session)
    perm_service.grant_permission(user.id, "documents", "read")
    
    # Create the dependency
    permission_checker = require_permission("documents", "read")
    
    # Call the dependency - should not raise
    result = await permission_checker(current_user=user, db=db_session)
    assert result == user


async def test_require_permission_without_permission(db_session: Session):
    """Test that require_permission denies access when user lacks the permission."""
    # Create a user without any permissions
    user_repo = UserRepository(db_session)
    user = user_repo.create({
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "is_active": True
    })
    
    # Create a permission (but don't grant it to the user)
    perm_repo = PermissionRepository(db_session)
    perm_repo.create({
        "resource": "documents",
        "action": "read"
    })
    
    # Create the dependency
    permission_checker = require_permission("documents", "read")
    
    # Call the dependency - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await permission_checker(current_user=user, db=db_session)
    
    assert exc_info.value.status_code == 403
    assert "lacks required permission" in exc_info.value.detail


async def test_require_permission_with_role_based_permission(db_session: Session):
    """Test that require_permission allows access via role-based permissions."""
    # Create a user
    user_repo = UserRepository(db_session)
    user = user_repo.create({
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "is_active": True
    })
    
    # Create a permission
    perm_repo = PermissionRepository(db_session)
    permission = perm_repo.create({
        "resource": "documents",
        "action": "read"
    })
    
    # Create a role with the permission
    role_service = RoleService(db_session)
    role = role_service.create_role("reader", [permission.id], "Reader role")
    
    # Assign role to user
    role_service.assign_role(user.id, role.id)
    
    # Refresh user to get updated roles
    db_session.refresh(user)
    
    # Create the dependency
    permission_checker = require_permission("documents", "read")
    
    # Call the dependency - should not raise
    result = await permission_checker(current_user=user, db=db_session)
    assert result == user


async def test_require_admin_with_admin_role(db_session: Session):
    """Test that require_admin allows access when user has admin role."""
    # Create a user
    user_repo = UserRepository(db_session)
    user = user_repo.create({
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "password_hash": "hashed_password",
        "is_active": True
    })
    
    # Create admin role
    role_service = RoleService(db_session)
    admin_role = role_service.create_role("admin", [], "Administrator role")
    
    # Assign admin role to user
    role_service.assign_role(user.id, admin_role.id)
    
    # Refresh user to get updated roles
    db_session.refresh(user)
    
    # Call the dependency - should not raise
    result = await require_admin(current_user=user, db=db_session)
    assert result == user


async def test_require_admin_without_admin_role(db_session: Session):
    """Test that require_admin denies access when user lacks admin role."""
    # Create a user without admin role
    user_repo = UserRepository(db_session)
    user = user_repo.create({
        "first_name": "Regular",
        "last_name": "User",
        "email": "user@example.com",
        "password_hash": "hashed_password",
        "is_active": True
    })
    
    # Create a non-admin role
    role_service = RoleService(db_session)
    user_role = role_service.create_role("user", [], "Regular user role")
    
    # Assign non-admin role to user
    role_service.assign_role(user.id, user_role.id)
    
    # Refresh user to get updated roles
    db_session.refresh(user)
    
    # Call the dependency - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=user, db=db_session)
    
    assert exc_info.value.status_code == 403
    assert "Admin role required" in exc_info.value.detail


async def test_require_admin_case_insensitive(db_session: Session):
    """Test that require_admin checks admin role case-insensitively."""
    # Create a user
    user_repo = UserRepository(db_session)
    user = user_repo.create({
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "password_hash": "hashed_password",
        "is_active": True
    })
    
    # Create admin role with different casing
    role_service = RoleService(db_session)
    admin_role = role_service.create_role("Admin", [], "Administrator role")
    
    # Assign admin role to user
    role_service.assign_role(user.id, admin_role.id)
    
    # Refresh user to get updated roles
    db_session.refresh(user)
    
    # Call the dependency - should not raise
    result = await require_admin(current_user=user, db=db_session)
    assert result == user
