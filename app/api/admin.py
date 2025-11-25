"""Admin API endpoints for role and permission management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.api.dependencies import require_admin
from app.api.schemas import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    MessageResponse
)
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService
from app.repositories.permission_repository import PermissionRepository
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Role management endpoints

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all roles.
    
    Requires admin role.
    
    Requirements: 9.1, 9.5
    """
    role_service = RoleService(db)
    roles = role_service.get_all_roles()
    return roles


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new role with permissions.
    
    Requires admin role.
    
    Requirements: 9.1, 9.2, 9.5
    """
    role_service = RoleService(db)
    
    try:
        role = role_service.create_role(
            name=role_data.name,
            permission_ids=role_data.permission_ids,
            description=role_data.description
        )
        return role
    except Exception as e:
        # Handle duplicate role name or other errors
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{role_data.name}' already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get role details by ID.
    
    Requires admin role.
    
    Requirements: 9.1, 9.5
    """
    role_service = RoleService(db)
    role = role_service.get_role(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role_permissions(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a role's permissions.
    
    Requires admin role.
    
    Requirements: 9.1, 9.3, 9.5
    """
    role_service = RoleService(db)
    role = role_service.update_role_permissions(role_id, role_update.permission_ids)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return role


@router.delete("/roles/{role_id}", response_model=MessageResponse)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a role.
    
    Requires admin role.
    
    Requirements: 9.1, 9.4, 9.5
    """
    role_service = RoleService(db)
    success = role_service.delete_role(role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return MessageResponse(message=f"Role {role_id} deleted successfully")



# Permission management endpoints

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all permissions.
    
    Requires admin role.
    
    Requirements: 7.1, 9.1, 9.5
    """
    permission_repo = PermissionRepository(db)
    permissions = permission_repo.get_all()
    return permissions


@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new permission.
    
    Requires admin role.
    
    Requirements: 7.1, 9.1, 9.5
    """
    permission_repo = PermissionRepository(db)
    
    # Check if permission already exists
    existing = permission_repo.get_by_resource_action(
        permission_data.resource,
        permission_data.action
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Permission '{permission_data.resource}:{permission_data.action}' already exists"
        )
    
    try:
        permission = permission_repo.create({
            "resource": permission_data.resource,
            "action": permission_data.action,
            "description": permission_data.description
        })
        return permission
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/permissions/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get permission details by ID.
    
    Requires admin role.
    
    Requirements: 7.1, 9.1, 9.5
    """
    permission_repo = PermissionRepository(db)
    permission = permission_repo.get_by_id(permission_id)
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    
    return permission


@router.delete("/permissions/{permission_id}", response_model=MessageResponse)
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a permission.
    
    Requires admin role.
    
    Requirements: 7.1, 9.1, 9.5
    """
    permission_repo = PermissionRepository(db)
    success = permission_repo.delete(permission_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    
    return MessageResponse(message=f"Permission {permission_id} deleted successfully")



# User-role assignment endpoints

@router.post("/users/{user_id}/roles/{role_id}", response_model=MessageResponse)
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Assign a role to a user.
    
    Requires admin role.
    
    Requirements: 6.2, 9.5
    """
    role_service = RoleService(db)
    success = role_service.assign_role(user_id, role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} or Role {role_id} not found"
        )
    
    return MessageResponse(message=f"Role {role_id} assigned to user {user_id}")


@router.delete("/users/{user_id}/roles/{role_id}", response_model=MessageResponse)
async def revoke_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Revoke a role from a user.
    
    Requires admin role.
    
    Requirements: 6.3, 9.5
    """
    role_service = RoleService(db)
    success = role_service.revoke_role(user_id, role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} or Role {role_id} not found"
        )
    
    return MessageResponse(message=f"Role {role_id} revoked from user {user_id}")



# User-permission assignment endpoints

@router.post("/users/{user_id}/permissions/{permission_id}", response_model=MessageResponse)
async def grant_permission_to_user(
    user_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Grant a direct permission to a user.
    
    Requires admin role.
    
    Requirements: 7.2, 9.5
    """
    # Get the permission to extract resource and action
    permission_repo = PermissionRepository(db)
    permission = permission_repo.get_by_id(permission_id)
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission {permission_id} not found"
        )
    
    permission_service = PermissionService(db)
    success = permission_service.grant_permission(
        user_id,
        permission.resource,
        permission.action
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    return MessageResponse(message=f"Permission {permission_id} granted to user {user_id}")


@router.delete("/users/{user_id}/permissions/{permission_id}", response_model=MessageResponse)
async def revoke_permission_from_user(
    user_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Revoke a direct permission from a user.
    
    Requires admin role.
    
    Requirements: 7.3, 9.5
    """
    # Get the permission to extract resource and action
    permission_repo = PermissionRepository(db)
    permission = permission_repo.get_by_id(permission_id)
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission {permission_id} not found"
        )
    
    permission_service = PermissionService(db)
    success = permission_service.revoke_permission(
        user_id,
        permission.resource,
        permission.action
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    return MessageResponse(message=f"Permission {permission_id} revoked from user {user_id}")
