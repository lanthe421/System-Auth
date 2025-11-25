"""Repository for session management operations."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
import hashlib


class SessionRepository:
    """
    Repository for managing user sessions.
    
    Requirements: 2.4, 3.1, 3.2
    """
    
    def __init__(self, db: Session):
        """
        Initialize the session repository.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def _hash_token(self, token: str) -> str:
        """
        Hash a token for secure storage.
        
        Args:
            token: The token to hash
            
        Returns:
            The hashed token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def create_session(self, user_id: int, token: str, expires_at: datetime) -> SessionModel:
        """
        Create a new session for a user.
        
        Args:
            user_id: The ID of the user
            token: The authentication token
            expires_at: When the session expires
            
        Returns:
            The created session
            
        Requirements: 2.4, 3.1
        """
        token_hash = self._hash_token(token)
        
        session = SessionModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_valid=True
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_session(self, token: str) -> Optional[SessionModel]:
        """
        Retrieve a session by token.
        
        Args:
            token: The authentication token
            
        Returns:
            The session if found and valid, None otherwise
            
        Requirements: 2.4, 3.1
        """
        token_hash = self._hash_token(token)
        
        session = self.db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash,
            SessionModel.is_valid == True,
            SessionModel.expires_at > datetime.utcnow()
        ).first()
        
        return session
    
    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a session (logout).
        
        Args:
            token: The authentication token
            
        Returns:
            True if session was invalidated, False if not found
            
        Requirements: 3.1, 3.2
        """
        token_hash = self._hash_token(token)
        
        session = self.db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash
        ).first()
        
        if session:
            session.is_valid = False
            self.db.commit()
            return True
        
        return False
    
    def invalidate_user_sessions(self, user_id: int) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Number of sessions invalidated
            
        Requirements: 3.1, 3.2
        """
        count = self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.is_valid == True
        ).update({"is_valid": False})
        
        self.db.commit()
        return count
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from the database.
        
        Returns:
            Number of sessions deleted
            
        Requirements: 3.1
        """
        count = self.db.query(SessionModel).filter(
            SessionModel.expires_at < datetime.utcnow()
        ).delete()
        
        self.db.commit()
        return count
