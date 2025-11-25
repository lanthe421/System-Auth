"""Repository for permission management operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.permission import Permission
from app.models.user import User, user_permissions
from app.models.role import role_permissions


class PermissionRepository:
    """
    Repository for managing permissions.
    
    Requirements: 7.1, 7.2, 7.3, 8.4
    """
    
    def __init__(self, db: Session):
        """
        Initialize the permission repository.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(self, permission_data: dict) -> Permission:
        """
        Create a new permission.
        
        Args:
            permission_data: Dictionary containing permission fields (resource, action, description)
            
        Returns:
            The created permission
            
        Raises:
            IntegrityError: If resource+action combination already exists
            
        Requirements: 7.1
        """
        permission = Permission(**permission_data)
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission
    
    def get_by_id(self, permission_id: int) -> Optional[Permission]:
        """
        Retrieve a permission by ID.
        
        Args:
            permission_id: The ID of the permission
            
        Returns:
            The permission if found, None otherwise
            
        Requirements: 7.1
        """
        return self.db.query(Permission).filter(Permission.id == permission_id).first()
    
    def get_by_resource_action(self, resource: str, action: str) -> Optional[Permission]:
        """
        Retrieve a permission by resource and action.
        
        Args:
            resource: The resource name
            action: The action name
            
        Returns:
            The permission if found, None otherwise
            
        Requirements: 7.1, 8.4
        """
        return self.db.query(Permission).filter(
            Permission.resource == resource,
            Permission.action == action
        ).first()
    
    def delete(self, permission_id: int) -> bool:
        """
        Delete a permission.
        
        Args:
            permission_id: The ID of the permission to delete
            
        Returns:
            True if permission was deleted, False if not found
            
        Requirements: 7.3
        """
        permission = self.get_by_id(permission_id)
        if not permission:
            return False
        
        self.db.delete(permission)
        self.db.commit()
        return True
    
    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """
        Get all permissions for a user (both direct and role-based).
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of unique permissions the user has access to
            
        Requirements: 7.2, 8.4
        """
        # Get user with all relationships loaded
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return []
        
        # Collect all permissions from direct grants
        permissions_set = set()
        
        # Add direct permissions
        for permission in user.permissions:
            permissions_set.add(permission.id)
        
        # Add permissions from roles
        for role in user.roles:
            for permission in role.permissions:
                permissions_set.add(permission.id)
        
        # Fetch all unique permissions
        if not permissions_set:
            return []
        
        return self.db.query(Permission).filter(Permission.id.in_(permissions_set)).all()
    
    def get_all(self) -> List[Permission]:
        """
        Get all permissions.
        
        Returns:
            List of all permissions
            
        Requirements: 7.1
        """
        return self.db.query(Permission).all()
