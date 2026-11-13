import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.security import hash_password
from app.middleware.tenant import TenantIsolationMiddleware, SecurityHeadersMiddleware
from app.models.models import (
    User,
    UserRole,
    SubscriptionPlanModel,
    SubscriptionPlan,
)
from app.api import (
    auth_router,
    organizations_router,
    users_router,
    departments_router,
    people_router,
    shifts_router,
    cameras_router,
    attendance_router,
    corrections_router,
    analytics_router,
    reports_router,
    notifications_router,
    admin_router,
    faces_router,
    recognition_router,
    recognition_ws_router,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("attendora")


async def seed_initial_data():
    """Seeds the default super admin account and subscription tiers if missing."""
    async with AsyncSessionLocal() as db:
        try:
            # 1. Super Admin Account
            admin_res = await db.execute(
                select(User).where(User.email == settings.SUPER_ADMIN_EMAIL.lower())
            )
            if not admin_res.scalar_one_or_none():
                super_admin = User(
                    email=settings.SUPER_ADMIN_EMAIL.lower(),
                    hashed_password=hash_password(settings.SUPER_ADMIN_PASSWORD),
                    full_name="ATTENDORA Super Admin",
                    role=UserRole.SUPER_ADMIN,
                    is_active=True,
                )
                db.add(super_admin)
                logger.info(f"Initialized super admin: {settings.SUPER_ADMIN_EMAIL}")

            # 2. Subscription Plans
            plans = [
                {
                    "name": "Free Tier",
                    "plan_type": SubscriptionPlan.FREE,
                    "max_people": 25,
                    "max_cameras": 1,
                    "max_admins": 1,
                    "price_monthly": 0.0,
                    "price_yearly": 0.0,
                    "features": ["Face Recognition", "Daily Attendance", "Webcam Support"],
                },
                {
                    "name": "Starter Plan",
                    "plan_type": SubscriptionPlan.STARTER,
                    "max_people": 100,
                    "max_cameras": 3,
                    "max_admins": 3,
                    "price_monthly": 49.0,
                    "price_yearly": 490.0,
                    "features": ["Face Recognition", "CSV/Excel Export", "Department Tracking", "Shift Management"],
                },
                {
                    "name": "Professional Plan",
                    "plan_type": SubscriptionPlan.PROFESSIONAL,
                    "max_people": 500,
                    "max_cameras": 10,
                    "max_admins": 10,
                    "price_monthly": 149.0,
                    "price_yearly": 1490.0,
                    "features": ["RTSP Camera Streams", "Anti-Spoofing Liveness", "PDF Reports", "Audit Logs"],
                },
                {
                    "name": "Enterprise Plan",
                    "plan_type": SubscriptionPlan.ENTERPRISE,
                    "max_people": 5000,
                    "max_cameras": 50,
                    "max_admins": 50,
                    "price_monthly": 499.0,
                    "price_yearly": 4990.0,
                    "features": ["Unlimited Teams", "Custom Data Retention", "Priority Queue", "24/7 SLA Support"],
                },
            ]

            for plan_info in plans:
                p_check = await db.execute(
                    select(SubscriptionPlanModel).where(SubscriptionPlanModel.name == plan_info["name"])
                )
                if not p_check.scalar_one_or_none():
                    new_plan = SubscriptionPlanModel(**plan_info)
                    db.add(new_plan)

            await db.commit()
            logger.info("Database seed checks completed successfully")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error seeding initial database records: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    try:
        await init_db()
        await seed_initial_data()
    except Exception as e:
        logger.warning(f"Database initialization warning (DB may not be connected yet): {e}")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Face Recognition Attendance Management SaaS Platform API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middlewares
# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Tenant Isolation
app.add_middleware(TenantIsolationMiddleware)

# Mount Uploads directory for static access
try:
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
except Exception:
    pass

# Include all API Routers
app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(users_router)
app.include_router(departments_router)
app.include_router(people_router)
app.include_router(shifts_router)
app.include_router(cameras_router)
app.include_router(attendance_router)
app.include_router(corrections_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(faces_router)
app.include_router(recognition_router)
app.include_router(recognition_ws_router)


# Health & Info Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "documentation": "/docs",
        "status": "operational",
    }


# Live Broadcast WebSocket Placeholder
@app.websocket("/ws/live/{org_id}")
async def live_events_ws(websocket: WebSocket, org_id: str):
    await websocket.accept()
    logger.info(f"Live events WebSocket connected for org {org_id}")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "ack",
                "org_id": org_id,
                "received": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        logger.info(f"Live events WebSocket disconnected for org {org_id}")
