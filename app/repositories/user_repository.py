"""Repository for user management operations."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User


class UserRepository:
    """
    Repository for managing user data.
    
    Requirements: 1.1, 1.2, 4.1, 4.2, 5.1
    """
    
    def __init__(self, db: Session):
        """
        Initialize the user repository.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(self, user_data: dict) -> User:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary containing user fields
            
        Returns:
            The created user
            
        Raises:
            IntegrityError: If email already exists
            
        Requirements: 1.1, 1.2
        """
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The user if found, None otherwise
            
        Requirements: 4.1
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email.
        
        Args:
            email: The email address
            
        Returns:
            The user if found, None otherwise
            
        Requirements: 1.2, 4.2
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def update(self, user_id: int, update_data: dict) -> Optional[User]:
        """
        Update a user's information.
        
        Args:
            user_id: The ID of the user to update
            update_data: Dictionary containing fields to update
            
        Returns:
            The updated user if found, None otherwise
            
        Raises:
            IntegrityError: If email update conflicts with existing email
            
        Requirements: 4.1, 4.2
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def soft_delete(self, user_id: int) -> bool:
        """
        Soft delete a user by setting is_active to False.
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if user was deleted, False if not found
            
        Requirements: 5.1
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True
    
    def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if an email already exists in the database.
        
        Args:
            email: The email to check
            exclude_user_id: Optional user ID to exclude from the check (for updates)
            
        Returns:
            True if email exists, False otherwise
            
        Requirements: 1.2, 4.2
        """
        query = self.db.query(User).filter(User.email == email)
        
        if exclude_user_id is not None:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is not None
