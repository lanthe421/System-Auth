"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, Callable

from app.database import get_db
from app.utils.jwt import get_user_id_from_token
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.services.permission_service import PermissionService
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that validates token and returns the current user.
    
    This dependency:
    - Extracts the token from the Authorization header
    - Validates the token format and signature
    - Checks if the session is still valid (not logged out)
    - Retrieves and returns the user
    - Raises 401 errors for missing, invalid, or expired tokens
    
    Args:
        authorization: The Authorization header (Bearer token)
        db: Database session
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: 401 if authentication fails
        
    Requirements: 2.5, 4.4, 8.3
    """
    # Check if authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if it's a Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token
    token = authorization.split(" ")[1]
    
    # Validate token and extract user ID
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if session is still valid (not logged out)
    session_repo = SessionRepository(db)
    session = session_repo.get_session(token)
    if not session or not session.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get the user
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def require_permission(resource: str, action: str) -> Callable:
    """
    FastAPI dependency factory that checks if current user has required permission.
    
    This dependency:
    - Requires the user to be authenticated (via get_current_user)
    - Checks if the user has the specified permission (via role or direct grant)
    - Returns 401 if user is not authenticated
    - Returns 403 if user lacks the required permission
    
    Args:
        resource: The resource name (e.g., "documents", "projects")
        action: The action name (e.g., "read", "create", "update", "delete")
        
    Returns:
        A dependency function that validates the permission
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if lacking permission
        
    Requirements: 8.1, 8.2, 8.3
    
    Example:
        @app.get("/api/resources/documents", dependencies=[Depends(require_permission("documents", "read"))])
        async def get_documents():
            return {"documents": [...]}
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """
        Check if the current user has the required permission.
        
        Args:
            current_user: The authenticated user (from get_current_user dependency)
            db: Database session
            
        Returns:
            The authenticated user if they have permission
            
        Raises:
            HTTPException: 403 if user lacks permission
        """
        # Check if user has the required permission
        permission_service = PermissionService(db)
        has_permission = permission_service.check_permission(
            user_id=current_user.id,
            resource=resource,
            action=action
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User lacks required permission: {resource}:{action}"
            )
        
        return current_user
    
    return permission_checker



async def require_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that checks if current user has admin role.
    
    This dependency:
    - Requires the user to be authenticated (via get_current_user)
    - Checks if the user has the "admin" role
    - Returns 401 if user is not authenticated
    - Returns 403 if user is not an admin
    
    Args:
        current_user: The authenticated user (from get_current_user dependency)
        db: Database session
        
    Returns:
        The authenticated user if they have admin role
        
    Raises:
        HTTPException: 403 if user is not admin
        
    Requirements: 9.5
    
    Example:
        @app.get("/api/admin/roles", dependencies=[Depends(require_admin)])
        async def get_roles():
            return {"roles": [...]}
    """
    # Check if user has admin role
    has_admin_role = any(role.name.lower() == "admin" for role in current_user.roles)
    
    if not has_admin_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to access this resource"
        )
    
    return current_user
