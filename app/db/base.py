# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import create_engine

# from app.db.base_class import Base
# # from app.models.tenant.tenant import Tenant
# from app.models.user.user import User
# # from app.models.hotel.hotel import Hotel

# # Tạo Base class
# Base = declarative_base()

# # Tạo engine (sẽ lấy config từ environment sau)
# DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/hotel_saas"
# engine = create_engine(DATABASE_URL)

# # Tạo SessionLocal
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Dependency để get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

from app.db.base_class import Base  # noqa
from app.models.user.user import User  # noqa
from app.models.user.customer import Customer  # noqa
from app.models.tenant.tenant import Tenant  # noqa
from app.models.hotel.hotel import Hotel  # noqa