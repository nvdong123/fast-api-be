# app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import logging
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.models.enums.user import UserRole
from app.schemas.auth import TokenPayload
from app.core.security import get_token_from_header, verify_token


# Setup logging
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def debug_token(token: str) -> None:
    try:
        # Split token to check header and payload
        parts = token.split('.')
        if len(parts) != 3:
            logger.error("Token does not have 3 parts")
            return

        # Decode header
        header = jwt.get_unverified_header(token)
        logger.debug(f"Token header: {header}")
        
        # Try to decode payload without verification
        payload = jwt.get_unverified_claims(token)
        logger.debug(f"Token payload (unverified): {payload}")
        
        return {
            "header": header,
            "payload": payload
        }
    except Exception as e:
        logger.error(f"Error debugging token: {str(e)}")
        return None

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_header)
) -> User:
    try:
        # print(token)
        payload = verify_token(token, token_type="access")
        user = db.query(User).filter(User.id == payload["sub"]).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    logger.debug(f"Checking superuser permissions for user: {current_user.id}")
    if current_user.role != UserRole.SUPER_ADMIN:
        logger.warning(f"Unauthorized superadmin access attempt by user: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_tenant_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    logger.debug(f"Checking tenant admin permissions for user: {current_user.id}")
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        logger.warning(
            f"Unauthorized tenant admin access attempt by user: {current_user.id} "
            f"with role: {current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# # Helper function to verify token without raising exceptions
# async def verify_token(token: str) -> Optional[dict]:
#     try:
#         return jwt.decode(
#             token,
#             settings.SECRET_KEY,
#             algorithms=[settings.ALGORITHM]
#         )
#     except Exception as e:
#         logger.error(f"Token verification failed: {str(e)}")
#         return None