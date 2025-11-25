"""Service for user management operations."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.utils.password import hash_password
from app.models.user import User


class UserService:
    """
    Service for user management business logic.
    
    Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 5.1, 5.4
    """
    
    def __init__(self, db: Session):
        """
        Initialize the user service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
    
    def register_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        password_confirm: str,
        middle_name: Optional[str] = None
    ) -> User:
        """
        Register a new user with validation.
        
        Args:
            first_name: User's first name
            last_name: User's last name
            email: User's email address
            password: User's password
            password_confirm: Password confirmation
            middle_name: User's middle name (optional)
            
        Returns:
            The created user
            
        Raises:
            ValueError: If validation fails
            IntegrityError: If email already exists
            
        Requirements: 1.1, 1.2, 1.3
        """
        # Validate password match
        if password != password_confirm:
            raise ValueError("Passwords do not match")
        
        # Check if email already exists
        if self.user_repo.email_exists(email):
            raise ValueError("Email already exists")
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Create user data
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "email": email,
            "password_hash": password_hash,
            "is_active": True
        }
        
        # Create the user
        user = self.user_repo.create(user_data)
        
        return user
    
    def update_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Optional[User]:
        """
        Update a user's profile information.
        
        Args:
            user_id: The ID of the user to update
            first_name: New first name (optional)
            last_name: New last name (optional)
            middle_name: New middle name (optional)
            email: New email address (optional)
            password: New password (optional)
            
        Returns:
            The updated user if found, None otherwise
            
        Raises:
            ValueError: If email already exists for another user
            
        Requirements: 4.1, 4.2
        """
        # Check if user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        # Validate email uniqueness if email is being updated
        if email and email != user.email:
            if self.user_repo.email_exists(email, exclude_user_id=user_id):
                raise ValueError("Email already exists")
        
        # Build update data
        update_data = {}
        
        if first_name is not None:
            update_data["first_name"] = first_name
        
        if last_name is not None:
            update_data["last_name"] = last_name
        
        if middle_name is not None:
            update_data["middle_name"] = middle_name
        
        if email is not None:
            update_data["email"] = email
        
        if password is not None:
            update_data["password_hash"] = hash_password(password)
        
        # Update the user
        if update_data:
            return self.user_repo.update(user_id, update_data)
        
        return user
    
    def delete_account(self, user_id: int) -> bool:
        """
        Soft delete a user account and invalidate all sessions.
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if user was deleted, False if not found
            
        Requirements: 5.1, 5.4
        """
        # Soft delete the user
        deleted = self.user_repo.soft_delete(user_id)
        
        if deleted:
            # Invalidate all user sessions
            self.session_repo.invalidate_user_sessions(user_id)
        
        return deleted
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The user if found, None otherwise
        """
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: The email address
            
        Returns:
            The user if found, None otherwise
        """
        return self.user_repo.get_by_email(email)
