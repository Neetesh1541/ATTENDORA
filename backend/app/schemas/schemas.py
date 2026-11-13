from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Generic, TypeVar
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.models import (
    OrgStatus,
    UserRole,
    PersonStatus,
    FaceRegStatus,
    AttendanceStatus,
    AttendanceAction,
    CorrectionStatus,
    CameraStatus,
    NotificationType,
    SubscriptionPlan,
    SubscriptionStatus,
)

T = TypeVar("T")


# ─── Generic & Common Schemas ────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    pages: int
    items: List[T]


# ─── Auth & Token Schemas ────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 28800  # in seconds (8 hours)


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    role: Optional[str] = None
    org_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: Optional[OrganizationResponse] = None


class RegisterRequest(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=255)
    org_slug: Optional[str] = Field(None, max_length=255)
    org_type: str = Field("general", max_length=100)
    timezone: str = Field("UTC", max_length=50)
    admin_name: str = Field(..., min_length=2, max_length=255)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=500)


# ─── Organization Schemas ────────────────────────────────────────────────────

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    org_type: Optional[str] = Field("general", max_length=100)
    logo_url: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    settings: Optional[Dict[str, Any]] = None
    working_days: Optional[List[str]] = None
    working_hours_start: Optional[str] = Field("09:00", max_length=10)
    working_hours_end: Optional[str] = Field("17:00", max_length=10)
    timezone: Optional[str] = Field("UTC", max_length=50)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    org_type: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    settings: Optional[Dict[str, Any]] = None
    working_days: Optional[List[str]] = None
    working_hours_start: Optional[str] = Field(None, max_length=10)
    working_hours_end: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)


class OrganizationStatusUpdate(BaseModel):
    status: OrgStatus


class OrganizationResponse(OrganizationBase):
    id: UUID
    status: OrgStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    total: int
    items: List[OrganizationResponse]


class OrganizationStatsResponse(BaseModel):
    total_people: int = 0
    total_users: int = 0
    total_departments: int = 0
    total_cameras: int = 0
    total_active_shifts: int = 0
    today_present: int = 0
    today_absent: int = 0
    today_late: int = 0
    attendance_rate: float = 0.0


# ─── User Schemas ────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=500)
    role: Optional[UserRole] = UserRole.MEMBER
    is_active: Optional[bool] = True
    person_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=500)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    person_id: Optional[UUID] = None


class UserResponse(UserBase):
    id: UUID
    organization_id: Optional[UUID] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    items: List[UserResponse]


# ─── Department Schemas ──────────────────────────────────────────────────────

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    head_person_id: Optional[UUID] = None
    is_active: Optional[bool] = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    head_person_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    organization_id: UUID
    member_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentListResponse(BaseModel):
    total: int
    items: List[DepartmentResponse]


# ─── Team Schemas ────────────────────────────────────────────────────────────

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    department_id: Optional[UUID] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    department_id: Optional[UUID] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    id: UUID
    organization_id: UUID
    member_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamListResponse(BaseModel):
    total: int
    items: List[TeamResponse]


# ─── Designation Schemas ─────────────────────────────────────────────────────

class DesignationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    level: Optional[int] = 0


class DesignationCreate(DesignationBase):
    pass


class DesignationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    level: Optional[int] = None


class DesignationResponse(DesignationBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DesignationListResponse(BaseModel):
    total: int
    items: List[DesignationResponse]


# ─── Shift Schemas ───────────────────────────────────────────────────────────

class ShiftBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    start_time: str = Field(..., max_length=10)  # "09:00"
    end_time: str = Field(..., max_length=10)    # "17:00"
    grace_period_minutes: Optional[int] = 15
    is_overnight: Optional[bool] = False
    is_active: Optional[bool] = True


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    grace_period_minutes: Optional[int] = None
    is_overnight: Optional[bool] = None
    is_active: Optional[bool] = None


class ShiftResponse(ShiftBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShiftListResponse(BaseModel):
    total: int
    items: List[ShiftResponse]


# ─── Holiday Schemas ─────────────────────────────────────────────────────────

class HolidayBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    date: date
    is_optional: Optional[bool] = False


class HolidayCreate(HolidayBase):
    pass


class HolidayUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    date: Optional[date] = None
    is_optional: Optional[bool] = None


class HolidayResponse(HolidayBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HolidayListResponse(BaseModel):
    total: int
    items: List[HolidayResponse]


# ─── Person Category Schemas ─────────────────────────────────────────────────

class PersonCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class PersonCategoryCreate(PersonCategoryBase):
    pass


class PersonCategoryResponse(PersonCategoryBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Person Schemas ──────────────────────────────────────────────────────────

class PersonBase(BaseModel):
    unique_id: str = Field(..., min_length=1, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    profile_photo_url: Optional[str] = Field(None, max_length=500)
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    category: Optional[str] = Field("employee", max_length=50)
    shift_id: Optional[UUID] = None
    joining_date: Optional[date] = None
    status: Optional[PersonStatus] = PersonStatus.ACTIVE
    custom_fields: Optional[Dict[str, Any]] = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    unique_id: Optional[str] = Field(None, min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    profile_photo_url: Optional[str] = Field(None, max_length=500)
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    category: Optional[str] = Field(None, max_length=50)
    shift_id: Optional[UUID] = None
    joining_date: Optional[date] = None
    status: Optional[PersonStatus] = None
    face_registered: Optional[FaceRegStatus] = None
    custom_fields: Optional[Dict[str, Any]] = None


class PersonResponse(PersonBase):
    id: UUID
    organization_id: UUID
    face_registered: FaceRegStatus
    department_name: Optional[str] = None
    team_name: Optional[str] = None
    designation_name: Optional[str] = None
    shift_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonListResponse(BaseModel):
    total: int
    items: List[PersonResponse]


class PersonBulkImportRow(BaseModel):
    unique_id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    category: Optional[str] = "employee"


class PersonBulkImportRequest(BaseModel):
    people: List[PersonBulkImportRow]


class PersonBulkImportResponse(BaseModel):
    imported: int
    failed: int
    errors: List[str] = []


# ─── Face Profile Schemas ────────────────────────────────────────────────────

class FaceProfileBase(BaseModel):
    image_url: Optional[str] = None
    quality_score: Optional[float] = None


class FaceProfileCreate(BaseModel):
    person_id: UUID
    encoding: Optional[bytes] = None
    image_url: Optional[str] = None
    quality_score: Optional[float] = None


class FaceProfileResponse(FaceProfileBase):
    id: UUID
    person_id: UUID
    organization_id: UUID
    registered_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaceConsentCreate(BaseModel):
    person_id: UUID
    consent_given: bool = True
    ip_address: Optional[str] = None


# ─── Camera Schemas ──────────────────────────────────────────────────────────

class CameraBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    camera_type: Optional[str] = Field("webcam", max_length=50)
    stream_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = True
    settings: Optional[Dict[str, Any]] = None


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    camera_type: Optional[str] = Field(None, max_length=50)
    stream_url: Optional[str] = Field(None, max_length=500)
    status: Optional[CameraStatus] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class CameraStatusUpdate(BaseModel):
    status: CameraStatus


class CameraResponse(CameraBase):
    id: UUID
    organization_id: UUID
    status: CameraStatus
    last_active: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraListResponse(BaseModel):
    total: int
    items: List[CameraResponse]


# ─── Attendance Session Schemas ──────────────────────────────────────────────

class AttendanceSessionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    session_date: date
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    session_type: Optional[str] = Field("general", max_length=50)
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    is_active: Optional[bool] = True


class AttendanceSessionCreate(AttendanceSessionBase):
    pass


class AttendanceSessionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    session_date: Optional[date] = None
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    session_type: Optional[str] = Field(None, max_length=50)
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class AttendanceSessionResponse(AttendanceSessionBase):
    id: UUID
    organization_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    record_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class AttendanceSessionListResponse(BaseModel):
    total: int
    items: List[AttendanceSessionResponse]


# ─── Attendance Record Schemas ───────────────────────────────────────────────

class AttendanceRecordBase(BaseModel):
    person_id: UUID
    session_id: Optional[UUID] = None
    date: date
    status: Optional[AttendanceStatus] = AttendanceStatus.PRESENT
    action: Optional[AttendanceAction] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    total_hours: Optional[float] = None
    is_late: Optional[bool] = False
    late_minutes: Optional[int] = 0
    is_early_departure: Optional[bool] = False
    early_departure_minutes: Optional[int] = 0
    overtime_minutes: Optional[int] = 0
    camera_id: Optional[UUID] = None
    recognition_confidence: Optional[float] = None
    marked_by: Optional[str] = "manual"
    notes: Optional[str] = None


class AttendanceRecordCreate(AttendanceRecordBase):
    pass


class AttendanceRecordUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    action: Optional[AttendanceAction] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    total_hours: Optional[float] = None
    is_late: Optional[bool] = None
    late_minutes: Optional[int] = None
    is_early_departure: Optional[bool] = None
    early_departure_minutes: Optional[int] = None
    overtime_minutes: Optional[int] = None
    notes: Optional[str] = None


class AttendanceRecordResponse(AttendanceRecordBase):
    id: UUID
    organization_id: UUID
    person_name: Optional[str] = None
    person_unique_id: Optional[str] = None
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceRecordListResponse(BaseModel):
    total: int
    items: List[AttendanceRecordResponse]


class AttendanceCheckInRequest(BaseModel):
    person_id: UUID
    session_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    check_in_time: Optional[datetime] = None
    notes: Optional[str] = None


class AttendanceCheckOutRequest(BaseModel):
    person_id: UUID
    session_id: Optional[UUID] = None
    camera_id: Optional[UUID] = None
    check_out_time: Optional[datetime] = None
    notes: Optional[str] = None


class AttendanceMarkRequest(BaseModel):
    person_id: UUID
    date: date
    status: AttendanceStatus = AttendanceStatus.PRESENT
    session_id: Optional[UUID] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    is_late: Optional[bool] = False
    late_minutes: Optional[int] = 0
    notes: Optional[str] = None


class TodaySummaryResponse(BaseModel):
    date: date
    total_people: int = 0
    present: int = 0
    absent: int = 0
    late: int = 0
    half_day: int = 0
    on_leave: int = 0
    attendance_percentage: float = 0.0
    recent_records: List[AttendanceRecordResponse] = []


# ─── Attendance Correction Schemas ───────────────────────────────────────────

class AttendanceCorrectionCreate(BaseModel):
    attendance_record_id: UUID
    requested_status: AttendanceStatus
    requested_check_in: Optional[datetime] = None
    requested_check_out: Optional[datetime] = None
    reason: str = Field(..., min_length=3)


class AttendanceCorrectionReview(BaseModel):
    review_notes: Optional[str] = None


class AttendanceCorrectionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    attendance_record_id: UUID
    requested_by: UUID
    original_status: AttendanceStatus
    requested_status: AttendanceStatus
    original_check_in: Optional[datetime] = None
    requested_check_in: Optional[datetime] = None
    original_check_out: Optional[datetime] = None
    requested_check_out: Optional[datetime] = None
    reason: str
    status: CorrectionStatus
    reviewed_by: Optional[UUID] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    requester_name: Optional[str] = None
    person_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceCorrectionListResponse(BaseModel):
    total: int
    items: List[AttendanceCorrectionResponse]


# ─── Notification Schemas ────────────────────────────────────────────────────

class NotificationCreate(BaseModel):
    user_id: Optional[UUID] = None
    type: NotificationType
    title: str = Field(..., max_length=255)
    message: str
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: Optional[UUID] = None
    type: NotificationType
    title: str
    message: str
    is_read: bool
    data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    total: int
    items: List[NotificationResponse]


class UnreadCountResponse(BaseModel):
    unread_count: int


# ─── Subscription & Plan Schemas ─────────────────────────────────────────────

class SubscriptionPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    plan_type: SubscriptionPlan
    max_people: int = 50
    max_cameras: int = 2
    max_admins: int = 2
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    features: Optional[List[str]] = None
    is_active: Optional[bool] = True


class SubscriptionPlanResponse(BaseModel):
    id: UUID
    name: str
    plan_type: SubscriptionPlan
    max_people: int
    max_cameras: int
    max_admins: int
    price_monthly: float
    price_yearly: float
    features: Optional[List[str]] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionPlanListResponse(BaseModel):
    total: int
    items: List[SubscriptionPlanResponse]


class OrganizationSubscriptionCreate(BaseModel):
    plan_id: UUID
    start_date: date
    end_date: Optional[date] = None
    status: Optional[SubscriptionStatus] = SubscriptionStatus.ACTIVE


class OrganizationSubscriptionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    plan_id: Optional[UUID] = None
    status: SubscriptionStatus
    start_date: date
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    plan: Optional[SubscriptionPlanResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Analytics Schemas ───────────────────────────────────────────────────────

class AnalyticsOverviewResponse(BaseModel):
    total_members: int = 0
    present_today: int = 0
    absent_today: int = 0
    late_today: int = 0
    on_leave_today: int = 0
    attendance_percentage: float = 0.0
    active_cameras: int = 0
    total_cameras: int = 0
    pending_corrections: int = 0


class DailyTrendItem(BaseModel):
    date: str
    present: int = 0
    absent: int = 0
    late: int = 0
    attendance_rate: float = 0.0


class AnalyticsTrendsResponse(BaseModel):
    trends: List[DailyTrendItem] = []


class DepartmentAnalyticsItem(BaseModel):
    department_id: Optional[UUID] = None
    department_name: str
    total_members: int = 0
    present: int = 0
    absent: int = 0
    attendance_rate: float = 0.0


class ShiftAnalyticsItem(BaseModel):
    shift_id: Optional[UUID] = None
    shift_name: str
    total_assigned: int = 0
    on_time: int = 0
    late: int = 0
    absent: int = 0


class CameraAnalyticsItem(BaseModel):
    camera_id: UUID
    camera_name: str
    location: Optional[str] = None
    status: CameraStatus
    total_detections: int = 0
    total_recognized: int = 0
    accuracy_rate: float = 0.0


class AdminStatsResponse(BaseModel):
    total_organizations: int = 0
    active_organizations: int = 0
    total_users: int = 0
    total_people: int = 0
    total_attendance_today: int = 0
    total_cameras: int = 0
    active_subscriptions: int = 0


# ─── Report Schemas ──────────────────────────────────────────────────────────

class ReportDailyResponse(BaseModel):
    date: date
    records: List[AttendanceRecordResponse] = []
    summary: Dict[str, Any] = {}


class ReportMonthlyResponse(BaseModel):
    year: int
    month: int
    total_days: int
    summary: Dict[str, Any] = {}
    department_breakdown: List[Dict[str, Any]] = []


class ReportCustomResponse(BaseModel):
    start_date: date
    end_date: date
    total_records: int
    records: List[AttendanceRecordResponse] = []
    summary: Dict[str, Any] = {}


# ─── Audit Log Schemas ───────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]
