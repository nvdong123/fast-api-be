# app/api/v1/endpoints/users.py
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils.email import send_new_account_email
from app.utils.upload import upload_file_to_storage


router = APIRouter()

@router.get("/", response_model=schemas.user.UserPagination)
def read_users(
    db: Session = Depends(deps.get_db),
    page: int = Query(0, ge=0),
    size: int = Query(10, gt=0),
    search: Optional[str] = Query(None),
    role: Optional[models.enums.UserRole] = Query(None),
    tenant_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve users with pagination and filters.
    """
    try:
        # print("Request headers:", request.headers)  # Debug log
        # current_user = models.User = Depends(deps.get_current_user)
        # print("Current user:", Depends(deps.get_current_user))  # Debug log
        # Super admin can see all users or filter by tenant
        if current_user.role == models.enums.user.UserRole.SUPER_ADMIN:
            users = crud.user_crud.get_multi_paginated(
                db,
                page=page,
                size=size,
                search=search,
                role=role,
                tenant_id=tenant_id,
                is_active=is_active
            )
        # Tenant admin can only see users from their tenant
        elif current_user.role == models.enums.user.UserRole.TENANT_ADMIN:
            users = crud.user_crud.get_multi_paginated(
                db,
                page=page,
                size=size,
                search=search,
                role=role,
                tenant_id=current_user.tenant_id,
                is_active=is_active
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return users
    except Exception as e:
        print(f"Error in read_users: {str(e)}")  # Debug log
        raise

@router.post("/", response_model=schemas.user.UserResponse)
def create_user(
    user_in: schemas.user.UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),  # Đổi dependency
) -> Any:
    """
    Create new user.
    """
    # Check permissions
    if current_user.role not in [models.enums.user.UserRole.SUPER_ADMIN, models.enums.user.UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Tenant admin can only create users for their tenant
    if current_user.role == models.enums.user.UserRole.TENANT_ADMIN:
        user_in.tenant_id = current_user.tenant_id
        # Cannot create super admin
        if user_in.role == models.enums.user.UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create super admin"
            )

    try:
        # print(user_in)
        user = crud.user_crud.create(db, obj_in=user_in)
        
        if settings.EMAILS_ENABLED:
            send_new_account_email(
                email_to=user_in.email,
                username=user_in.full_name,
                password=user_in.password
            )
            
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
@router.put("/me", response_model=schemas.user.UserResponse)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    full_name: Optional[str] = Body(None),
    email: Optional[str] = Body(None),
    phone: Optional[str] = Body(None),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update own user.
    """
    current_user_data = schemas.user.UserUpdate(
        full_name=full_name or current_user.full_name,
        email=email or current_user.email,
        phone=phone or current_user.phone
    )
    try:
        user = crud.user_crud.update(db, db_obj=current_user, obj_in=current_user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return user

@router.get("/me", response_model=schemas.user.UserResponse)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.user.UserResponse)
def read_user_by_id(
    user_id: str,
    current_user: models.User = Depends(deps.get_current_tenant_admin),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # Check permissions
    if current_user.role != models.enums.user.UserRole.SUPER_ADMIN:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    return user


@router.patch("/{user_id}", response_model=schemas.user.UserResponse)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    user_in: schemas.user.UserUpdate,
    current_user: models.User = Depends(deps.get_current_tenant_admin),
) -> Any:
    """
    Update a user.
    """
    user = crud.user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role != models.enums.user.UserRole.SUPER_ADMIN:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        # Cannot change tenant_id
        if user_in.tenant_id and user_in.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change user's tenant"
            )
        # Cannot change role to super admin
        if user_in.role == models.enums.user.UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to assign super admin role"
            )

    try:
        user = crud.user_crud.update(db, db_obj=user, obj_in=user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return user

@router.post("/{user_id}/change-password", status_code=status.HTTP_200_OK)
def change_password(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    password_in: schemas.user.ChangePassword,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Change user password.
    """
    # Only allow changing own password unless super admin
    if current_user.id != user_id and current_user.role != models.enums.user.UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    user = crud.user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not crud.user_crud.verify_password(password_in.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    user_in = schemas.user.UserUpdate(password=password_in.new_password)
    crud.user_crud.update(db, db_obj=user, obj_in=user_in)
    return {"message": "Password updated successfully"}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    email_in: schemas.user.ForgotPassword,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Password recovery email.
    """
    user = crud.user_crud.get_by_email(db, email=email_in.email)
    if user:
        # Generate password reset token
        token = generate_password_reset_token(email_in.email)
        if settings.EMAILS_ENABLED:
            send_reset_password_email(
                email_to=email_in.email,
                username=user.full_name,
                token=token
            )
    return {"message": "Password recovery email sent"}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    *,
    db: Session = Depends(deps.get_db),
    reset_in: schemas.user.ResetPassword,
) -> Any:
    """
    Reset password with token.
    """
    email = verify_password_reset_token(reset_in.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
        
    user = crud.user_crud.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_in = schemas.user.UserUpdate(password=reset_in.new_password)
    crud.user_crud.update(db, db_obj=user, obj_in=user_in)
    return {"message": "Password updated successfully"}

@router.delete("/{user_id}", response_model=schemas.user.UserResponse)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    current_user: models.User = Depends(deps.get_current_tenant_admin),
) -> Any:
    """
    Delete a user.
    """
    user = crud.user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role != models.enums.user.UserRole.SUPER_ADMIN:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        # Cannot delete super admin
        if user.role == models.enums.user.UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete super admin user"
            )

    user = crud.user_crud.delete(db, id=user_id)
    return user

@router.patch("/{user_id}/activate", response_model=schemas.user.UserResponse)
def activate_user(
    user_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_tenant_admin),
) -> Any:
    """
    Activate a user.
    """
    user = crud.user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    if current_user.role != models.enums.user.UserRole.SUPER_ADMIN:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

    user_in = schemas.user.UserUpdate(is_active=True)
    user = crud.user_crud.update(db, db_obj=user, obj_in=user_in)
    return user

@router.patch("/{user_id}/deactivate", response_model=schemas.user.UserResponse)
def deactivate_user(
    user_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_tenant_admin),
) -> Any:
    """
    Deactivate a user.
    """
    user = crud.user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    if current_user.role != models.enums.user.UserRole.SUPER_ADMIN:
        if user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        # Cannot deactivate super admin
        if user.role == models.enums.user.UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot deactivate super admin user"
            )

    user_in = schemas.user.UserUpdate(is_active=False)
    user = crud.user_crud.update(db, db_obj=user, obj_in=user_in)
    return user

@router.post("/upload-avatar", response_model=schemas.user.UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Upload user avatar.
    """
    try:
        avatar_url = await upload_file_to_storage(file, f"avatars/{current_user.id}")
        user_in = schemas.user.UserUpdate(avatar=avatar_url)
        user = crud.user_crud.update(db, db_obj=current_user, obj_in=user_in)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error uploading avatar: {str(e)}"
        )


@router.get("/test-token")
async def test_token(
    current_user: models.User = Depends(deps.get_current_user)
    ):
    return {
        "msg": "Token is valid",
        "user_id": current_user.id,
        "role": current_user.role
    }