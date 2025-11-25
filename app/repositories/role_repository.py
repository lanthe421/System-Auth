"""Repository for role management operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.role import Role, role_permissions
from app.models.permission import Permission
from app.models.user import User, user_roles


class RoleRepository:
    """
    Repository for managing roles.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 9.4
    """
    
    def __init__(self, db: Session):
        """
        Initialize the role repository.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(self, role_data: dict, permission_ids: Optional[List[int]] = None) -> Role:
        """
        Create a new role with optional permissions.
        
        Args:
            role_data: Dictionary containing role fields (name, description)
            permission_ids: Optional list of permission IDs to associate with the role
            
        Returns:
            The created role
            
        Raises:
            IntegrityError: If role name already exists
            
        Requirements: 6.1, 9.2
        """
        role = Role(**role_data)
        
        # Add permissions if provided
        if permission_ids:
            permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
            role.permissions = permissions
        
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def get_by_id(self, role_id: int) -> Optional[Role]:
        """
        Retrieve a role by ID.
        
        Args:
            role_id: The ID of the role
            
        Returns:
            The role if found, None otherwise
            
        Requirements: 6.1
        """
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_by_name(self, name: str) -> Optional[Role]:
        """
        Retrieve a role by name.
        
        Args:
            name: The name of the role
            
        Returns:
            The role if found, None otherwise
            
        Requirements: 6.1
        """
        return self.db.query(Role).filter(Role.name == name).first()
    
    def update(self, role_id: int, update_data: dict) -> Optional[Role]:
        """
        Update a role's information (name, description).
        
        Args:
            role_id: The ID of the role to update
            update_data: Dictionary containing fields to update
            
        Returns:
            The updated role if found, None otherwise
            
        Raises:
            IntegrityError: If name update conflicts with existing role name
            
        Requirements: 6.4
        """
        role = self.get_by_id(role_id)
        if not role:
            return None
        
        for key, value in update_data.items():
            if hasattr(role, key) and key != 'permissions':
                setattr(role, key, value)
        
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def delete(self, role_id: int) -> bool:
        """
        Delete a role and all its associations.
        
        Args:
            role_id: The ID of the role to delete
            
        Returns:
            True if role was deleted, False if not found
            
        Requirements: 9.4
        """
        role = self.get_by_id(role_id)
        if not role:
            return False
        
        self.db.delete(role)
        self.db.commit()
        return True
    
    def add_permissions_to_role(self, role_id: int, permission_ids: List[int]) -> Optional[Role]:
        """
        Add permissions to a role.
        
        Args:
            role_id: The ID of the role
            permission_ids: List of permission IDs to add
            
        Returns:
            The updated role if found, None otherwise
            
        Requirements: 6.1, 6.4
        """
        role = self.get_by_id(role_id)
        if not role:
            return None
        
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        
        # Add only new permissions (avoid duplicates)
        existing_permission_ids = {p.id for p in role.permissions}
        for permission in permissions:
            if permission.id not in existing_permission_ids:
                role.permissions.append(permission)
        
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def remove_permissions_from_role(self, role_id: int, permission_ids: List[int]) -> Optional[Role]:
        """
        Remove permissions from a role.
        
        Args:
            role_id: The ID of the role
            permission_ids: List of permission IDs to remove
            
        Returns:
            The updated role if found, None otherwise
            
        Requirements: 6.4
        """
        role = self.get_by_id(role_id)
        if not role:
            return None
        
        # Remove specified permissions
        role.permissions = [p for p in role.permissions if p.id not in permission_ids]
        
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def set_role_permissions(self, role_id: int, permission_ids: List[int]) -> Optional[Role]:
        """
        Set the exact permissions for a role (replaces existing permissions).
        
        Args:
            role_id: The ID of the role
            permission_ids: List of permission IDs to set
            
        Returns:
            The updated role if found, None otherwise
            
        Requirements: 6.4, 9.3
        """
        role = self.get_by_id(role_id)
        if not role:
            return None
        
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        role.permissions = permissions
        
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: The ID of the user
            role_id: The ID of the role
            
        Returns:
            True if role was assigned, False if user or role not found
            
        Requirements: 6.2
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        role = self.get_by_id(role_id)
        
        if not user or not role:
            return False
        
        # Check if user already has this role
        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()
        
        return True
    
    def revoke_role_from_user(self, user_id: int, role_id: int) -> bool:
        """
        Revoke a role from a user.
        
        Args:
            user_id: The ID of the user
            role_id: The ID of the role
            
        Returns:
            True if role was revoked, False if user or role not found
            
        Requirements: 6.3
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        role = self.get_by_id(role_id)
        
        if not user or not role:
            return False
        
        # Remove role if user has it
        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()
        
        return True
    
    def get_user_roles(self, user_id: int) -> List[Role]:
        """
        Get all roles assigned to a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of roles assigned to the user
            
        Requirements: 6.2
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return []
        
        return user.roles
    
    def get_all(self) -> List[Role]:
        """
        Get all roles.
        
        Returns:
            List of all roles
            
        Requirements: 6.1, 9.1
        """
        return self.db.query(Role).all()
