# app/scripts/seed_data.py
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.enums.user import UserRole
from app.core.security import get_password_hash
from app.models.enums.tenant import TenantStatus, SubscriptionPlan

def seed_data(db: Session):
    # Create demo tenants
    demo_tenant_1 = Tenant(
        name="Hotel Chain A",
        subdomain="hotel-chain-a",
        description="First demo hotel chain",
        contact_email="admin@hotel-chain-a.com",
        contact_phone="+84123456789",
        status=TenantStatus.ACTIVE,
        subscription_plan=SubscriptionPlan.ENTERPRISE,
        subscription_start=datetime.utcnow(),
        subscription_end=datetime.utcnow() + timedelta(days=365),
        is_active=True,
        max_users=20,
        max_hotels=10,
        timezone="Asia/Ho_Chi_Minh",
        locale="vi"
    )
    db.add(demo_tenant_1)

    demo_tenant_2 = Tenant(
        name="Hotel Chain B",
        subdomain="hotel-chain-b",
        description="Second demo hotel chain",
        contact_email="admin@hotel-chain-b.com",
        contact_phone="+84987654321",
        status=TenantStatus.ACTIVE,
        subscription_plan=SubscriptionPlan.PREMIUM,
        subscription_start=datetime.utcnow(),
        subscription_end=datetime.utcnow() + timedelta(days=180),
        is_active=True,
        max_users=10,
        max_hotels=5,
        timezone="Asia/Ho_Chi_Minh",
        locale="vi"
    )
    db.add(demo_tenant_2)
    db.flush()  # To get tenant IDs

    # Create demo users
    # 1. Super Admin
    super_admin = User(
        email="superadmin@example.com",
        password=get_password_hash("superadmin123"),
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        phone="+84123456789"
    )
    db.add(super_admin)

    # 2. Tenant Admins
    tenant_admin_1 = User(
        email="admin1@hotel-chain-a.com",
        password=get_password_hash("tenadmin123"),
        full_name="Tenant Admin A",
        role=UserRole.TENANT_ADMIN,
        tenant_id=demo_tenant_1.id,
        is_active=True,
        phone="+84123456790"
    )
    db.add(tenant_admin_1)

    tenant_admin_2 = User(
        email="admin2@hotel-chain-b.com",
        password=get_password_hash("tenadmin123"),
        full_name="Tenant Admin B",
        role=UserRole.TENANT_ADMIN,
        tenant_id=demo_tenant_2.id,
        is_active=True,
        phone="+84123456791"
    )
    db.add(tenant_admin_2)

    # 3. Staff users
    staff_1 = User(
        email="staff1@hotel-chain-a.com",
        password=get_password_hash("staff123"),
        full_name="Staff A",
        role=UserRole.STAFF,
        tenant_id=demo_tenant_1.id,
        is_active=True,
        phone="+84123456792"
    )
    db.add(staff_1)

    staff_2 = User(
        email="staff2@hotel-chain-b.com",
        password=get_password_hash("staff123"),
        full_name="Staff B",
        role=UserRole.STAFF,
        tenant_id=demo_tenant_2.id,
        is_active=True,
        phone="+84123456793"
    )
    db.add(staff_2)

    # Commit all changes
    try:
        db.commit()
        print("Successfully seeded demo data!")
        print("\nDemo Accounts:")
        print("1. Super Admin:")
        print("   - Email: superadmin@example.com")
        print("   - Password: superadmin123")
        print("\n2. Tenant Admins:")
        print("   - Email: admin1@hotel-chain-a.com")
        print("   - Password: tenadmin123")
        print("   - Email: admin2@hotel-chain-b.com")
        print("   - Password: tenadmin123")
        print("\n3. Staff:")
        print("   - Email: staff1@hotel-chain-a.com")
        print("   - Password: staff123")
        print("   - Email: staff2@hotel-chain-b.com")
        print("   - Password: staff123")
    except Exception as e:
        print(f"Error seeding data: {str(e)}")
        db.rollback()
        raise

def main():
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()