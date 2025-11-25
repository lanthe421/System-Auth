"""Service for authentication operations."""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.utils.password import hash_password, verify_password
from app.utils.jwt import generate_access_token, generate_refresh_token, verify_token, get_user_id_from_token
from app.models.user import User
from app.models.role import Role
from app.config import settings


class AuthService:
    """
    Service for authentication business logic.
    
    Requirements: 1.1, 1.4, 1.5, 2.1, 2.2, 2.3, 3.1, 3.2
    """
    
    def __init__(self, db: Session):
        """
        Initialize the authentication service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
    
    def register(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        password_confirm: str,
        middle_name: Optional[str] = None
    ) -> User:
        """
        Register a new user with password hashing and default role assignment.
        
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
            ValueError: If validation fails or email already exists
            
        Requirements: 1.1, 1.4, 1.5
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
        
        # Assign default role (user role)
        default_role = self.db.query(Role).filter(Role.name == "user").first()
        if default_role:
            user.roles.append(default_role)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def login(self, email: str, password: str) -> Tuple[str, str, User]:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            ValueError: If credentials are invalid or user is inactive
            
        Requirements: 2.1, 2.2, 2.3
        """
        # Get user by email
        user = self.user_repo.get_by_email(email)
        
        # Check if user exists
        if not user:
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is inactive")
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Generate tokens
        access_token = generate_access_token(user.id)
        refresh_token = generate_refresh_token(user.id)
        
        # Create session for access token
        access_expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.session_repo.create_session(user.id, access_token, access_expires_at)
        
        return access_token, refresh_token, user
    
    def logout(self, token: str) -> bool:
        """
        Invalidate user session (logout).
        
        Args:
            token: The authentication token to invalidate
            
        Returns:
            True if session was invalidated, False if not found
            
        Requirements: 3.1, 3.2
        """
        return self.session_repo.invalidate_session(token)
    
    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            ValueError: If refresh token is invalid
            
        Requirements: 2.1, 3.1
        """
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise ValueError("Invalid refresh token")
        
        # Get user ID from token
        user_id = int(payload.get("sub"))
        
        # Verify user exists and is active
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Invalid refresh token")
        
        # Generate new tokens
        new_access_token = generate_access_token(user_id)
        new_refresh_token = generate_refresh_token(user_id)
        
        # Create session for new access token
        access_expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.session_repo.create_session(user_id, new_access_token, access_expires_at)
        
        return new_access_token, new_refresh_token
    
    def verify_token_and_get_user(self, token: str) -> Optional[User]:
        """
        Verify token and return the associated user.
        
        Args:
            token: The authentication token
            
        Returns:
            The user if token is valid, None otherwise
            
        Requirements: 2.5
        """
        # Check if session exists and is valid
        session = self.session_repo.get_session(token)
        if not session:
            return None
        
        # Get user
        user = self.user_repo.get_by_id(session.user_id)
        if not user or not user.is_active:
            return None
        
        return user
