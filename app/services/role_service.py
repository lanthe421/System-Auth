"""Service for role management operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.role_repository import RoleRepository
from app.models.role import Role


class RoleService:
    """
    Service for role management business logic.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 9.4
    """
    
    def __init__(self, db: Session):
        """
        Initialize the role service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.role_repo = RoleRepository(db)
    
    def create_role(self, name: str, permission_ids: List[int], description: Optional[str] = None) -> Role:
        """
        Create a new role with permissions.
        
        Args:
            name: The name of the role
            permission_ids: List of permission IDs to associate with the role
            description: Optional description of the role
            
        Returns:
            The created role
            
        Raises:
            IntegrityError: If role name already exists
            
        Requirements: 6.1, 9.2
        """
        role_data = {
            "name": name,
            "description": description
        }
        
        return self.role_repo.create(role_data, permission_ids)
    
    def assign_role(self, user_id: int, role_id: int) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: The ID of the user
            role_id: The ID of the role
            
        Returns:
            True if role was assigned, False if user or role not found
            
        Requirements: 6.2
        """
        return self.role_repo.assign_role_to_user(user_id, role_id)
    
    def revoke_role(self, user_id: int, role_id: int) -> bool:
        """
        Revoke a role from a user.
        
        Args:
            user_id: The ID of the user
            role_id: The ID of the role
            
        Returns:
            True if role was revoked, False if user or role not found
            
        Requirements: 6.3
        """
        return self.role_repo.revoke_role_from_user(user_id, role_id)
    
    def update_role_permissions(self, role_id: int, permission_ids: List[int]) -> Optional[Role]:
        """
        Update a role's permissions (replaces existing permissions).
        
        Args:
            role_id: The ID of the role
            permission_ids: List of permission IDs to set
            
        Returns:
            The updated role if found, None otherwise
            
        Requirements: 6.4, 9.3
        """
        return self.role_repo.set_role_permissions(role_id, permission_ids)
    
    def delete_role(self, role_id: int) -> bool:
        """
        Delete a role and all its associations.
        
        Args:
            role_id: The ID of the role to delete
            
        Returns:
            True if role was deleted, False if not found
            
        Requirements: 9.4
        """
        return self.role_repo.delete(role_id)
    
    def get_role(self, role_id: int) -> Optional[Role]:
        """
        Get a role by ID.
        
        Args:
            role_id: The ID of the role
            
        Returns:
            The role if found, None otherwise
        """
        return self.role_repo.get_by_id(role_id)
    
    def get_all_roles(self) -> List[Role]:
        """
        Get all roles.
        
        Returns:
            List of all roles
        """
        return self.role_repo.get_all()
