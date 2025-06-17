from sqlalchemy.orm import Session
from app.models.tenant.tenant import Tenant
from app.models.user.user import User
from app.models.hotel.hotel import Hotel
from app.models.enums.tenant import TenantStatus, SubscriptionPlan
from app.core.config import settings

def seed_db(db: Session) -> None:
    # First create tenant
    default_tenant = Tenant(
        name="Default Hotel Group",
        subdomain="default",
        status=TenantStatus.ACTIVE,
        subscription_plan=SubscriptionPlan.BASIC,
        is_active=True,
        max_users=10,
        max_hotels=5
    )
    db.add(default_tenant)
    db.commit()
    db.refresh(default_tenant)

    # Then create admin user
    admin_user = User(
        email=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
        is_superuser=True,
        tenant_id=default_tenant.id
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # Create sample hotel
    sample_hotel = Hotel(
        tenant_id=default_tenant.id,
        name="Sample Hotel",
        address="123 Sample Street",
        city="Sample City",
        country="Sample Country",
        status="draft",
        is_active=True
    )
    db.add(sample_hotel)
    db.commit()

if __name__ == "__main__":
    from app.db.session import SessionLocal
    db = SessionLocal()
    seed_db(db)
    db.close()