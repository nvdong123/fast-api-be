from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash
from app.models.enums.tenant import TenantStatus, SubscriptionPlan
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.tenant.tenant import Tenant
from app.models.user.user import User
from app.models.enums.tenant import TenantStatus, SubscriptionPlan
from app.models.enums.user import UserRole
from app.core.config import settings

def seed_db():
    db = SessionLocal()
    try:
        # Create System Admin Tenant
        system_tenant = Tenant(
            name="System Admin",
            subdomain="system-admin",
            description="System Administration Tenant",
            contact_email="system@admin.com",
            contact_phone="+84123456700",
            status=TenantStatus.ACTIVE,
            subscription_plan=SubscriptionPlan.ENTERPRISE,
            subscription_start=datetime.utcnow(),
            subscription_end=datetime.utcnow() + timedelta(days=3650),  # 10 years
            is_active=True,
            is_deleted=False,
            max_users=999,  # Unlimited
            max_hotels=999,  # Unlimited
            timezone="UTC",
            locale="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(system_tenant)
        db.flush()  # To get tenant ID

        # Create Super Admin user with system tenant
        super_admin = User(
            email="superadmin@example.com",
            password=get_password_hash("superadmin123"),
            full_name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            tenant_id=system_tenant.id,  # Link to system tenant
            is_active=True,
            is_deleted=False,
            phone="+84123456789",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(super_admin)

        # Create Demo Tenants
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
            is_deleted=False,
            max_users=20,
            max_hotels=10,
            timezone="Asia/Ho_Chi_Minh",
            locale="vi",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
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
            is_deleted=False,
            max_users=10,
            max_hotels=5,
            timezone="Asia/Ho_Chi_Minh",
            locale="vi",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(demo_tenant_2)
        db.flush()

        # Create tenant admins
        tenant_admin_1 = User(
            email="admin1@hotel-chain-a.com",
            password=get_password_hash("tenadmin123"),
            full_name="Tenant Admin A",
            role=UserRole.TENANT_ADMIN,
            tenant_id=demo_tenant_1.id,
            is_active=True,
            is_deleted=False,
            phone="+84123456790",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(tenant_admin_1)

        tenant_admin_2 = User(
            email="admin2@hotel-chain-b.com",
            password=get_password_hash("tenadmin123"),
            full_name="Tenant Admin B",
            role=UserRole.TENANT_ADMIN,
            tenant_id=demo_tenant_2.id,
            is_active=True,
            is_deleted=False,
            phone="+84123456791",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(tenant_admin_2)

        # Create staff users
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
        db.commit()
        print("Successfully seeded demo data!")
        print("\nDemo Accounts:")
        print("1. Super Admin (System Tenant):")
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
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()