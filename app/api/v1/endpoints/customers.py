from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.api import deps

# Import get_db
from app.schemas.customer import (
    CustomerResponse,  
    CustomerCreate, 
    CustomerUpdate,
    CustomerWithBookings
)
from app.crud.customer import customer_crud  # Giả sử bạn có crud operations

router = APIRouter()

@router.post("/", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(deps.get_db)
):
    return customer_crud.create(db=db, obj_in=customer)

@router.get("/", response_model=List[CustomerResponse])
def get_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return customer_crud.get_multi(db=db, skip=skip, limit=limit)

@router.get("/{customer_id}", response_model=CustomerWithBookings)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(deps.get_db)
):
    customer = customer_crud.get(db=db, id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    customer_in: CustomerUpdate,
    db: Session = Depends(deps.get_db)
):
    customer = customer_crud.get(db=db, id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_crud.update(db=db, db_obj=customer, obj_in=customer_in)

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(deps.get_db)
):
    customer = customer_crud.get(db=db, id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer_crud.remove(db=db, id=customer_id)
    return {"message": "Customer deleted successfully"}