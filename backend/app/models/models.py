import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, Date,
    ForeignKey, UniqueConstraint, Index, JSON, LargeBinary, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


# ─── Enums ────────────────────────────────────────────────────────────────

class OrgStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    PENDING = "pending"

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    MANAGER = "manager"
    MEMBER = "member"

class PersonStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class FaceRegStatus(str, enum.Enum):
    NOT_REGISTERED = "not_registered"
    REGISTERED = "registered"
    FAILED = "failed"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EARLY_DEPARTURE = "early_departure"
    HALF_DAY = "half_day"
    LEAVE = "leave"
    HOLIDAY = "holiday"
    WEEKLY_OFF = "weekly_off"

class AttendanceAction(str, enum.Enum):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"

class CorrectionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class CameraStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"

class NotificationType(str, enum.Enum):
    ATTENDANCE_MARKED = "attendance_marked"
    LATE_ARRIVAL = "late_arrival"
    MISSING_CHECKOUT = "missing_checkout"
    CORRECTION_REQUEST = "correction_request"
    CORRECTION_APPROVED = "correction_approved"
    CORRECTION_REJECTED = "correction_rejected"
    CAMERA_OFFLINE = "camera_offline"
    SYSTEM_ALERT = "system_alert"

class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"


def utcnow():
    return datetime.now(timezone.utc)


# ─── Organizations ────────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    org_type = Column(String(100), nullable=False, default="general")
    logo_url = Column(String(500))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    zip_code = Column(String(20))
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    status = Column(SAEnum(OrgStatus), default=OrgStatus.ACTIVE, nullable=False)
    settings = Column(JSON, default=dict)
    working_days = Column(JSON, default=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday"])
    working_hours_start = Column(String(10), default="09:00")
    working_hours_end = Column(String(10), default="17:00")
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    designations = relationship("Designation", back_populates="organization", cascade="all, delete-orphan")
    people = relationship("Person", back_populates="organization", cascade="all, delete-orphan")
    shifts = relationship("Shift", back_populates="organization", cascade="all, delete-orphan")
    holidays = relationship("Holiday", back_populates="organization", cascade="all, delete-orphan")
    cameras = relationship("Camera", back_populates="organization", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="organization", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="organization", cascade="all, delete-orphan")


# ─── Users (Login Accounts) ──────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    role = Column(SAEnum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True))
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="users")
    person = relationship("Person", foreign_keys=[person_id])


# ─── Departments ──────────────────────────────────────────────────────────

class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    head_person_id = Column(UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="departments")
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    people = relationship("Person", back_populates="department", foreign_keys="Person.department_id")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_dept_org_name"),
    )


# ─── Teams ────────────────────────────────────────────────────────────────

class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="teams")
    department = relationship("Department", back_populates="teams")
    people = relationship("Person", back_populates="team")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_team_org_name"),
    )


# ─── Designations ────────────────────────────────────────────────────────

class Designation(Base):
    __tablename__ = "designations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    level = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="designations")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_desig_org_name"),
    )


# ─── Shifts ───────────────────────────────────────────────────────────────

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    grace_period_minutes = Column(Integer, default=15)
    is_overnight = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="shifts")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_shift_org_name"),
    )


# ─── Holidays ─────────────────────────────────────────────────────────────

class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    is_optional = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="holidays")

    __table_args__ = (
        UniqueConstraint("organization_id", "date", name="uq_holiday_org_date"),
    )


# ─── People (Members of Organizations) ───────────────────────────────────

class Person(Base):
    __tablename__ = "people"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    unique_id = Column(String(100), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    profile_photo_url = Column(String(500))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    designation_id = Column(UUID(as_uuid=True), ForeignKey("designations.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(50), default="employee")
    shift_id = Column(UUID(as_uuid=True), ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    joining_date = Column(Date)
    status = Column(SAEnum(PersonStatus), default=PersonStatus.ACTIVE, nullable=False)
    face_registered = Column(SAEnum(FaceRegStatus), default=FaceRegStatus.NOT_REGISTERED, nullable=False)
    custom_fields = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="people")
    department = relationship("Department", back_populates="people", foreign_keys=[department_id])
    team = relationship("Team", back_populates="people")
    face_profile = relationship("FaceProfile", back_populates="person", uselist=False, cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="person", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "unique_id", name="uq_person_org_uid"),
        Index("ix_person_org_name", "organization_id", "full_name"),
        Index("ix_person_org_dept", "organization_id", "department_id"),
        Index("ix_person_org_status", "organization_id", "status"),
    )


# ─── Person Categories ───────────────────────────────────────────────────

class PersonCategory(Base):
    __tablename__ = "person_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_pcat_org_name"),
    )


# ─── Face Profiles ────────────────────────────────────────────────────────

class FaceProfile(Base):
    __tablename__ = "face_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE"), nullable=False, unique=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    encoding = Column(LargeBinary, nullable=False)  # Serialized face encoding (numpy array)
    image_url = Column(String(500))
    quality_score = Column(Float)
    registered_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    person = relationship("Person", back_populates="face_profile")

    __table_args__ = (
        Index("ix_face_org", "organization_id"),
    )


# ─── Face Registration Consents ───────────────────────────────────────────

class FaceRegistrationConsent(Base):
    __tablename__ = "face_registration_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    ip_address = Column(String(50))
    withdrawn = Column(Boolean, default=False)
    withdrawn_date = Column(DateTime(timezone=True))


# ─── Cameras ──────────────────────────────────────────────────────────────

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    camera_type = Column(String(50), default="webcam")  # webcam, ip, rtsp
    stream_url = Column(String(500))
    status = Column(SAEnum(CameraStatus), default=CameraStatus.OFFLINE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, default=dict)
    last_active = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="cameras")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_camera_org_name"),
    )


# ─── Attendance Sessions ─────────────────────────────────────────────────

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    session_date = Column(Date, nullable=False)
    start_time = Column(String(10))
    end_time = Column(String(10))
    session_type = Column(String(50), default="general")  # general, lecture, shift, event
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="attendance_sessions")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_session_org_date", "organization_id", "session_date"),
    )


# ─── Attendance Records ──────────────────────────────────────────────────

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("attendance_sessions.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, nullable=False)
    status = Column(SAEnum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False)
    action = Column(SAEnum(AttendanceAction), nullable=True)
    check_in_time = Column(DateTime(timezone=True))
    check_out_time = Column(DateTime(timezone=True))
    total_hours = Column(Float)
    is_late = Column(Boolean, default=False)
    late_minutes = Column(Integer, default=0)
    is_early_departure = Column(Boolean, default=False)
    early_departure_minutes = Column(Integer, default=0)
    overtime_minutes = Column(Integer, default=0)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    recognition_confidence = Column(Float)
    marked_by = Column(String(50), default="ai")  # ai, manual, import
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    organization = relationship("Organization")
    person = relationship("Person", back_populates="attendance_records")
    session = relationship("AttendanceSession", back_populates="records")

    __table_args__ = (
        Index("ix_att_org_date", "organization_id", "date"),
        Index("ix_att_person_date", "person_id", "date"),
        Index("ix_att_org_person_date", "organization_id", "person_id", "date"),
    )


# ─── Attendance Corrections ──────────────────────────────────────────────

class AttendanceCorrection(Base):
    __tablename__ = "attendance_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_record_id = Column(UUID(as_uuid=True), ForeignKey("attendance_records.id", ondelete="CASCADE"), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_status = Column(SAEnum(AttendanceStatus), nullable=False)
    requested_status = Column(SAEnum(AttendanceStatus), nullable=False)
    original_check_in = Column(DateTime(timezone=True))
    requested_check_in = Column(DateTime(timezone=True))
    original_check_out = Column(DateTime(timezone=True))
    requested_check_out = Column(DateTime(timezone=True))
    reason = Column(Text, nullable=False)
    status = Column(SAEnum(CorrectionStatus), default=CorrectionStatus.PENDING, nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_corr_org_status", "organization_id", "status"),
    )


# ─── Recognition Logs ────────────────────────────────────────────────────

class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    recognized = Column(Boolean, default=False, nullable=False)
    confidence = Column(Float)
    faces_detected = Column(Integer, default=0)
    faces_recognized = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_reclog_org_ts", "organization_id", "timestamp"),
    )


# ─── Notifications ───────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(SAEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="notifications")

    __table_args__ = (
        Index("ix_notif_user_read", "user_id", "is_read"),
    )


# ─── Audit Logs ───────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    details = Column(JSON, default=dict)
    ip_address = Column(String(50))
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_audit_org_ts", "organization_id", "timestamp"),
    )


# ─── Subscription Plans ──────────────────────────────────────────────────

class SubscriptionPlanModel(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    plan_type = Column(SAEnum(SubscriptionPlan), nullable=False)
    max_people = Column(Integer, default=50)
    max_cameras = Column(Integer, default=2)
    max_admins = Column(Integer, default=2)
    price_monthly = Column(Float, default=0.0)
    price_yearly = Column(Float, default=0.0)
    features = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


# ─── Organization Subscriptions ──────────────────────────────────────────

class OrganizationSubscription(Base):
    __tablename__ = "organization_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True)
    status = Column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
