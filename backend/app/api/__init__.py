from app.api.auth import router as auth_router
from app.api.organizations import router as organizations_router
from app.api.users import router as users_router
from app.api.departments import router as departments_router
from app.api.people import router as people_router
from app.api.shifts import router as shifts_router
from app.api.cameras import router as cameras_router
from app.api.attendance import router as attendance_router
from app.api.corrections import router as corrections_router
from app.api.analytics import router as analytics_router
from app.api.reports import router as reports_router
from app.api.notifications import router as notifications_router
from app.api.admin import router as admin_router
from app.api.faces import router as faces_router
from app.api.recognition import router as recognition_router, ws_router as recognition_ws_router

__all__ = [
    "auth_router",
    "organizations_router",
    "users_router",
    "departments_router",
    "people_router",
    "shifts_router",
    "cameras_router",
    "attendance_router",
    "corrections_router",
    "analytics_router",
    "reports_router",
    "notifications_router",
    "admin_router",
    "faces_router",
    "recognition_router",
    "recognition_ws_router",
]
