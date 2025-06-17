# app/api/v1/endpoints/tenants.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api import deps

from app.models.tenant.tenant import Tenant
from app.models.enums.tenant import TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse, TenantStatusUpdate

router = APIRouter()

@router.get("/", response_model=List[TenantResponse])
def get_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    tenants = db.query(Tenant).offset(skip).limit(limit).all()
    return tenants

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(deps.get_db)
):
    # Check if subdomain already exists
    if tenant.subdomain:
        existing_tenant = db.query(Tenant).filter(Tenant.subdomain == tenant.subdomain).first()
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subdomain already registered"
            )
    
    # Set subscription dates
    now = datetime.utcnow()
    subscription_end = now + timedelta(days=30)  # Default 30 days trial
    
    db_tenant = Tenant(
        **tenant.dict(),
        status=TenantStatus.PENDING,
        subscription_start=now,
        subscription_end=subscription_end
    )
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(deps.get_db)
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return tenant

@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    db: Session = Depends(deps.get_db)
):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check subdomain uniqueness if subdomain is being updated
    if tenant_update.subdomain and tenant_update.subdomain != db_tenant.subdomain:
        existing_tenant = db.query(Tenant).filter(Tenant.subdomain == tenant_update.subdomain).first()
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subdomain already registered"
            )
    
    update_data = tenant_update.dict(exclude_unset=True)
    
    # Update tenant attributes
    for field, value in update_data.items():
        setattr(db_tenant, field, value)
    
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(deps.get_db)
):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Soft delete
    db_tenant.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Tenant deleted successfully"}

@router.patch("/{tenant_id}/status", response_model=TenantResponse)
def update_tenant_status(
    tenant_id: str,
    status_update: TenantStatusUpdate,
    db: Session = Depends(deps.get_db)
):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    db_tenant.status = status_update.status
    
    # Update is_active based on status
    if status_update.status == TenantStatus.ACTIVE:
        db_tenant.activate()
    elif status_update.status == TenantStatus.SUSPENDED:
        db_tenant.suspend()
    
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.post("/{tenant_id}/extend-subscription", response_model=TenantResponse)
def extend_subscription(
    tenant_id: str,
    days: int,
    db: Session = Depends(deps.get_db)
):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    db_tenant.extend_subscription(days)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant