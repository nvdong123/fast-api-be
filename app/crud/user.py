# app/crud/user.py
from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.enums.user import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserPagination
from app.utils.validators import validate_password, validate_phone

class CRUDUser:
    def get(self, db: Session, id: str) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None
    ) -> Any:
        query = db.query(User)
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        # Validate password strength
        # validate_password(obj_in.password)
        if obj_in.phone:
            validate_phone(obj_in.phone)

        # Check email uniqueness
        if self.get_by_email(db, email=obj_in.email):
            raise ValueError("Email already registered")

        # Create user object
        db_obj = User(
            email=obj_in.email,
            password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            phone=obj_in.phone,
            role=obj_in.role,
            tenant_id=obj_in.tenant_id,
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        # Handle password update
        if "password" in update_data:
            # validate_password(update_data["password"])
            update_data["password"] = get_password_hash(update_data["password"])

        # Handle phone update
        if "phone" in update_data:
            validate_phone(update_data["phone"])

        # Handle email update
        if "email" in update_data and update_data["email"] != db_obj.email:
            if self.get_by_email(db, email=update_data["email"]):
                raise ValueError("Email already registered")

        # Update user object
        for field in update_data:
            setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: str) -> Optional[User]:
        obj = db.query(User).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.role == UserRole.SUPER_ADMIN

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def get_multi_paginated(
        self,
        db: Session,
        *,
        page: int = 0,
        size: int = 10,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        tenant_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> UserPagination:
        query = db.query(User)
        
        # Apply filters
        if search:
            search_filter = (
                User.full_name.ilike(f"%{search}%") |
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if role is not None:
            query = query.filter(User.role == role)
        
        if tenant_id is not None:
            query = query.filter(User.tenant_id == tenant_id)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(page * size).limit(size).all()
        
        # Calculate total pages
        pages = (total + size - 1) // size
        
        return {
            "items": users,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }

user_crud = CRUDUser()