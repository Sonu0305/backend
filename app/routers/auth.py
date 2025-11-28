from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..database import get_db
from ..models import User, PasswordResetToken
from ..schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenValidationResponse,
    MessageResponse,
    LoginResponse
)
from ..utils import (
    hash_password,
    verify_password,
    generate_reset_token,
    get_token_expiration,
    is_token_expired
)
from ..services.email_service import send_password_reset_email
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
    
    - **email**: User's email
    - **password**: User's password
    """
    # Find user
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    return {
        "message": "Login successful",
        "user": user
    }


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate password reset process
    
    Sends a password reset email to the user if the email exists.
    For security, always returns success even if email doesn't exist.
    
    - **email**: User's registered email address
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    # For security, don't reveal if email exists or not
    # Always return success message
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Invalidate any existing unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).update({"used_at": datetime.utcnow()})
    
    # Generate new reset token
    token = generate_reset_token()
    expires_at = get_token_expiration()
    
    # Save token to database
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    # Create reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    # Send email (don't wait for it to complete)
    try:
        await send_password_reset_email(user.email, reset_link)
    except Exception as e:
        # Log error but don't expose it to user
        print(f"Failed to send email: {str(e)}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.get("/validate-token/{token}", response_model=TokenValidationResponse)
async def validate_token(token: str, db: Session = Depends(get_db)):
    """
    Validate a password reset token
    
    - **token**: Password reset token from email
    """
    # Find token in database
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()
    
    if not reset_token:
        return {
            "valid": False,
            "message": "Invalid or expired token"
        }
    
    # Check if token has been used
    if reset_token.used_at:
        return {
            "valid": False,
            "message": "This reset link has already been used"
        }
    
    # Check if token has expired
    if is_token_expired(reset_token.expires_at):
        return {
            "valid": False,
            "message": "This reset link has expired"
        }
    
    # Get user email
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    
    return {
        "valid": True,
        "message": "Token is valid",
        "email": user.email if user else None
    }


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid token
    
    - **token**: Password reset token from email
    - **new_password**: New password (minimum 8 characters)
    """
    # Find token in database
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Check if token has been used
    if reset_token.used_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has already been used"
        )
    
    # Check if token has expired
    if is_token_expired(reset_token.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired"
        )
    
    # Get user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = hash_password(request.new_password)
    
    # Mark token as used
    reset_token.used_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password has been reset successfully"}
