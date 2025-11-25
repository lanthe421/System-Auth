"""User management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import UserService
from app.api.dependencies import get_current_user
from app.api.schemas import UserResponse, UserUpdate, MessageResponse
from app.models.user import User


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current authenticated user's profile.
    
    Requirements: 4.4
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current authenticated user's profile.
    
    Requirements: 4.1, 4.2, 4.3
    """
    user_service = UserService(db)
    
    try:
        # Update the user profile
        updated_user = user_service.update_profile(
            user_id=current_user.id,
            first_name=updates.first_name,
            last_name=updates.last_name,
            middle_name=updates.middle_name,
            email=updates.email,
            password=updates.password
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(updated_user)
        
    except ValueError as e:
        # Handle validation errors (e.g., duplicate email)
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


@router.delete("/me", response_model=MessageResponse)
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete the current authenticated user's account.
    
    This will:
    - Set the user's is_active field to False
    - Invalidate all active sessions (logout)
    - Retain all user data in the database
    
    Requirements: 5.1, 5.2
    """
    user_service = UserService(db)
    
    deleted = user_service.delete_account(current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return MessageResponse(message="Account successfully deleted")
