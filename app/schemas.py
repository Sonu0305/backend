from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset"""
    token: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class TokenValidationResponse(BaseModel):
    """Schema for token validation response"""
    valid: bool
    message: str
    email: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class LoginResponse(BaseModel):
    """Schema for login response"""
    message: str
    user: UserResponse
