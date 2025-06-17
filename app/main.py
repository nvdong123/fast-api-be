from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings


# Database models
from app.models.tenant import Tenant
from app.models.hotel import Hotel
from app.models.booking import Booking

# API Routes
from app.api.v1.endpoints import tenants, hotels, auth, bookings, customers, rooms, users, room_types, zalo


app = FastAPI(title="Hotel Booking SaaS")

# CORS setup
origins = [
    "http://ai.ailab.vn:3005",  # React admin
    "http://ai.ailab.vn:3006",
    "http://ai.ailab.vn:5001",  # Vite default port
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(
    tenants.router,
    prefix="/api/v1/tenants",
    tags=["tenants"]
)

app.include_router(
    hotels.router,
    prefix="/api/v1/hotels",
    tags=["hotels"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"]
)

app.include_router(
    bookings.router,
    prefix="/api/v1/bookings",
    tags=["bookings"]
)

app.include_router(
    customers.router,
    prefix="/api/v1/customers",
    tags=["customers"]
)

app.include_router(
    rooms.router,
    prefix="/api/v1/rooms",
    tags=["rooms"]
)

app.include_router(
    room_types.router,
    prefix="/api/v1/room-types",
    tags=["room-types"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)

app.include_router(
    zalo.router,
    prefix="/api/v1/zalo",
    tags=["zalo"]
)