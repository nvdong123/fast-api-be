from typing import List, Optional, Any

from sqlalchemy.orm import Session
from app.models.user.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from .base import CRUDBase

class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.email == email).first()

    def get_by_phone(self, db: Session, *, phone: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.phone == phone).first()
    
    def get_by_zalo_id(self, db: Session, *, zalo_id: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.zalo_id == zalo_id).first()

    def get_multi_with_bookings(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Customer]:
        return (
            db.query(Customer)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, db: Session, *, obj_in: CustomerCreate) -> Customer:
        # Custom validation before create
        if obj_in.email and self.get_by_email(db, email=obj_in.email):
            raise ValueError("Email already registered")
        if obj_in.phone and self.get_by_phone(db, phone=obj_in.phone):
            raise ValueError("Phone number already registered")
        if obj_in.zalo_id and self.get_by_zalo_id(db, zalo_id=obj_in.zalo_id):
            raise ValueError("Zalo ID already registered")
        
        return super().create(db, obj_in=obj_in)

    def update(
        self, 
        db: Session, 
        *,
        db_obj: Customer,
        obj_in: CustomerUpdate
    ) -> Customer:
        # Custom validation before update
        if obj_in.email and obj_in.email != db_obj.email:
            if self.get_by_email(db, email=obj_in.email):
                raise ValueError("Email already registered")
        if obj_in.phone and obj_in.phone != db_obj.phone:
            if self.get_by_phone(db, phone=obj_in.phone):
                raise ValueError("Phone number already registered")
        if obj_in.zalo_id and obj_in.zalo_id != db_obj.zalo_id:
            if self.get_by_zalo_id(db, zalo_id=obj_in.zalo_id):
                raise ValueError("Zalo ID already registered")

        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    def get_customer_with_bookings(
        self, db: Session, *, customer_id: Any
    ) -> Optional[Customer]:
        return (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

customer_crud = CRUDCustomer(Customer)