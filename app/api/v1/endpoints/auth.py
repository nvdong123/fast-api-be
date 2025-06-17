# app/api/v1/endpoints/auth.py
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import logging

from app.api import deps
from app.core import security
from app.core.config import settings
from app.schemas import auth, user
from app.models import User
from app.utils.email import send_reset_password_email

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=auth.Token)
async def login(
    login_data: auth.LoginRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Login for access token
    """
    try:
        # Verify user credentials
        user = db.query(User).filter(User.email == login_data.email).first()        
        if not user or not security.verify_password(login_data.password, user.password):
            # print(login_data.password)
            # print(user.password)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is inactive"
            )

        # Update last login time
        user.last_login = datetime.now()
        db.commit()

        # Create tokens
        access_token = security.create_access_token(
            subject=user.id,
            role=user.role,
            tenant_id=user.tenant_id
        )
        # print(access_token)
        refresh_token = security.create_refresh_token(
            subject=user.id,
            role=user.role,
            tenant_id=user.tenant_id
        )
        # print(refresh_token)

        logger.info(f"User {user.email} logged in successfully")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise

@router.post("/refresh-token", response_model=auth.Token)
async def refresh_token(
    db: Session = Depends(deps.get_db),
    refresh_token: str = Body(..., embed=True)
) -> Any:
    """
    Refresh access token using refresh token
    """
    try:
        # Verify refresh token
        payload = security.verify_token(refresh_token, token_type="refresh")
        user = db.query(User).filter(User.id == payload["sub"]).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Create new access token
        access_token = security.create_access_token(
            subject=user.id,
            role=user.role,
            tenant_id=user.tenant_id
        )

        logger.info(f"Access token refreshed for user {user.email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # Return same refresh token
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}")
        raise

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    email_in: auth.ForgotPassword,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Password recovery email
    """
    try:
        user = db.query(User).filter(User.email == email_in.email).first()
        if user:
            # Create password reset token
            reset_token = security.create_access_token(
                subject=user.id,
                role=user.role,
                tenant_id=user.tenant_id
            )
            
            # Update user reset token fields
            user.reset_token = reset_token
            user.reset_token_expires = datetime.now() + timedelta(
                hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
            )
            db.commit()

            # Send email
            await send_reset_password_email(
                email_to=user.email,
                token=reset_token,
                username=user.full_name
            )
            
            logger.info(f"Password reset email sent to {user.email}")

        # Always return success to prevent email enumeration
        return {"msg": "If email exists, password reset instructions have been sent"}
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: auth.ResetPassword,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Reset password using reset token
    """
    try:
        user = db.query(User).filter(
            User.reset_token == reset_data.token,
            User.reset_token_expires > datetime.now()
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )

        # Update password and clear reset token
        user.password = security.get_password_hash(reset_data.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()

        logger.info(f"Password reset successful for user {user.email}")
        return {"msg": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: auth.ChangePassword,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Change password (requires authentication)
    """
    try:
        if not security.verify_password(
            password_data.old_password, 
            current_user.password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )

        current_user.password = security.get_password_hash(password_data.new_password)
        db.commit()

        logger.info(f"Password changed successfully for user {current_user.email}")
        return {"msg": "Password updated successfully"}
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise

@router.get("/me", response_model=user.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get current user info (requires authentication)
    """
    return current_user