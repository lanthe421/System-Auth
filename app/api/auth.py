"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService
from app.api.schemas import (
    UserRegistration,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    MessageResponse
)


router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Requirements: 1.1, 1.2, 1.3
    """
    auth_service = AuthService(db)
    
    try:
        # Register the user
        user = auth_service.register(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            middle_name=user_data.middle_name,
            email=user_data.email,
            password=user_data.password,
            password_confirm=user_data.password_confirm
        )
        
        # Log the user in automatically
        access_token, refresh_token, _ = auth_service.login(
            email=user_data.email,
            password=user_data.password
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except ValueError as e:
        # Handle validation errors (duplicate email, password mismatch, etc.)
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return tokens.
    
    Requirements: 2.1, 2.2
    """
    auth_service = AuthService(db)
    
    try:
        access_token, refresh_token, user = auth_service.login(
            email=credentials.email,
            password=credentials.password
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except ValueError as e:
        # Handle authentication errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Logout user by invalidating their session.
    
    Requirements: 3.1
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    # Extract token from "Bearer <token>"
    token = authorization.split(" ")[1]
    
    auth_service = AuthService(db)
    success = auth_service.logout(token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Requirements: 2.1, 3.1
    """
    auth_service = AuthService(db)
    
    try:
        access_token, refresh_token = auth_service.refresh_token(
            refresh_data.refresh_token
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
