"""Service for permission management operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.permission_repository import PermissionRepository
from app.models.permission import Permission
from app.models.user import User, user_permissions


class PermissionService:
    """
    Service for permission management business logic.
    
    Requirements: 7.2, 7.3, 8.1, 8.2, 8.4, 8.5
    """
    
    def __init__(self, db: Session):
        """
        Initialize the permission service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.permission_repo = PermissionRepository(db)
    
    def check_permission(self, user_id: int, resource: str, action: str) -> bool:
        """
        Check if a user has permission to perform an action on a resource.
        Evaluates both role-based and direct permissions.
        
        Args:
            user_id: The ID of the user
            resource: The resource name
            action: The action name
            
        Returns:
            True if user has permission, False otherwise
            
        Requirements: 8.1, 8.2, 8.4, 8.5
        """
        # Get all user permissions (direct + role-based)
        user_permissions_list = self.permission_repo.get_user_permissions(user_id)
        
        # Check if any permission matches the resource and action
        for permission in user_permissions_list:
            if permission.resource == resource and permission.action == action:
                return True
        
        return False
    
    def grant_permission(self, user_id: int, resource: str, action: str) -> bool:
        """
        Grant a direct permission to a user.
        
        Args:
            user_id: The ID of the user
            resource: The resource name
            action: The action name
            
        Returns:
            True if permission was granted, False if user or permission not found
            
        Requirements: 7.2
        """
        # Get the user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Get or create the permission
        permission = self.permission_repo.get_by_resource_action(resource, action)
        if not permission:
            return False
        
        # Check if user already has this direct permission
        if permission not in user.permissions:
            user.permissions.append(permission)
            self.db.commit()
        
        return True
    
    def revoke_permission(self, user_id: int, resource: str, action: str) -> bool:
        """
        Revoke a direct permission from a user.
        
        Args:
            user_id: The ID of the user
            resource: The resource name
            action: The action name
            
        Returns:
            True if permission was revoked, False if user or permission not found
            
        Requirements: 7.3
        """
        # Get the user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Get the permission
        permission = self.permission_repo.get_by_resource_action(resource, action)
        if not permission:
            return False
        
        # Remove permission if user has it
        if permission in user.permissions:
            user.permissions.remove(permission)
            self.db.commit()
        
        return True
    
    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """
        Get all permissions for a user (both direct and role-based).
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of unique permissions the user has access to
            
        Requirements: 8.4, 8.5
        """
        return self.permission_repo.get_user_permissions(user_id)
