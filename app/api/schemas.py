"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, Field
import re


class UserRegistration(BaseModel):
    """
    Schema for user registration request.
    
    Requirements: 1.1, 1.3
    """
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="User's middle name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")
    password_confirm: str = Field(..., description="Password confirmation")
    
    @field_validator('first_name', 'last_name', 'middle_name')
    @classmethod
    def validate_name_fields(cls, v):
        """Validate name fields are not empty or just whitespace."""
        if v is not None and v.strip() == '':
            raise ValueError('Name fields cannot be empty or contain only whitespace')
        return v.strip() if v else v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Validate password meets minimum security requirements.
        
        Requirements: 1.4
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v
    
    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        """
        Validate that passwords match.
        
        Requirements: 1.3
        """
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLogin(BaseModel):
    """
    Schema for user login request.
    
    Requirements: 2.1
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")
    
    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v):
        """Validate password is not empty."""
        if v.strip() == '':
            raise ValueError('Password cannot be empty')
        return v


class TokenResponse(BaseModel):
    """
    Schema for token response.
    
    Requirements: 2.1
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """
    Schema for user response.
    
    Requirements: 1.1, 4.1
    """
    id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """
    Schema for user profile update request.
    
    All fields are optional - only provided fields will be updated.
    
    Requirements: 4.1
    """
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="User's middle name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="User's new password")
    
    @field_validator('first_name', 'last_name', 'middle_name')
    @classmethod
    def validate_name_fields(cls, v):
        """Validate name fields are not empty or just whitespace."""
        if v is not None and v.strip() == '':
            raise ValueError('Name fields cannot be empty or contain only whitespace')
        return v.strip() if v else v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Validate password meets minimum security requirements.
        
        Requirements: 4.3
        """
        if v is None:
            return v
        
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# Admin schemas for role and permission management

class PermissionCreate(BaseModel):
    """
    Schema for creating a permission.
    
    Requirements: 7.1, 9.1
    """
    resource: str = Field(..., min_length=1, max_length=100, description="Resource name")
    action: str = Field(..., min_length=1, max_length=50, description="Action name (e.g., read, create, update, delete)")
    description: Optional[str] = Field(None, max_length=500, description="Permission description")
    
    @field_validator('resource', 'action')
    @classmethod
    def validate_not_empty(cls, v):
        """Validate fields are not empty or just whitespace."""
        if v.strip() == '':
            raise ValueError('Field cannot be empty or contain only whitespace')
        return v.strip()
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is one of the standard CRUD operations."""
        valid_actions = ['create', 'read', 'update', 'delete']
        if v.lower() not in valid_actions:
            raise ValueError(f'Action must be one of: {", ".join(valid_actions)}')
        return v.lower()


class PermissionResponse(BaseModel):
    """
    Schema for permission response.
    
    Requirements: 7.1, 9.1
    """
    id: int
    resource: str
    action: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """
    Schema for creating a role.
    
    Requirements: 6.1, 9.1, 9.2
    """
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")
    permission_ids: list[int] = Field(default_factory=list, description="List of permission IDs to assign to this role")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty or just whitespace."""
        if v.strip() == '':
            raise ValueError('Role name cannot be empty or contain only whitespace')
        return v.strip()
    
    @field_validator('permission_ids')
    @classmethod
    def validate_permission_ids(cls, v):
        """Validate permission IDs are positive integers."""
        if v is not None:
            for pid in v:
                if pid <= 0:
                    raise ValueError('Permission IDs must be positive integers')
        return v


class RoleUpdate(BaseModel):
    """
    Schema for updating a role's permissions.
    
    Requirements: 6.4, 9.3
    """
    permission_ids: list[int] = Field(..., description="List of permission IDs to assign to this role")
    
    @field_validator('permission_ids')
    @classmethod
    def validate_permission_ids(cls, v):
        """Validate permission IDs are positive integers."""
        for pid in v:
            if pid <= 0:
                raise ValueError('Permission IDs must be positive integers')
        return v


class RoleResponse(BaseModel):
    """
    Schema for role response.
    
    Requirements: 6.1, 9.1, 9.2
    """
    id: int
    name: str
    description: Optional[str] = None
    permissions: list[PermissionResponse] = []
    
    class Config:
        from_attributes = True
