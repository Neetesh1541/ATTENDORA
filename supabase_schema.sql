-- =============================================================================
-- ATTENDORA — Supabase PostgreSQL Production Schema & Seed Migration
-- Compatible with Supabase SQL Editor, PostgreSQL 14+, Neon, and AWS RDS
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── 1. Custom Enum Types ────────────────────────────────────────────────────

DO $$ BEGIN
    CREATE TYPE org_status AS ENUM ('active', 'suspended', 'deactivated', 'pending');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('super_admin', 'org_admin', 'manager', 'member');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE person_status AS ENUM ('active', 'inactive', 'suspended');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE face_reg_status AS ENUM ('not_registered', 'registered', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE attendance_status AS ENUM ('present', 'absent', 'late', 'early_departure', 'half_day', 'leave', 'holiday', 'weekly_off');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE attendance_action AS ENUM ('check_in', 'check_out', 'break_start', 'break_end');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE correction_status AS ENUM ('pending', 'approved', 'rejected');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE camera_status AS ENUM ('online', 'offline', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_type AS ENUM ('attendance_marked', 'late_arrival', 'missing_checkout', 'correction_request', 'correction_approved', 'correction_rejected', 'camera_offline', 'system_alert');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_plan AS ENUM ('free', 'starter', 'professional', 'enterprise');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_status AS ENUM ('active', 'expired', 'cancelled', 'trial');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ─── 2. Organizations Table ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    org_type VARCHAR(100) NOT NULL DEFAULT 'general',
    logo_url VARCHAR(500),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    zip_code VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    status org_status NOT NULL DEFAULT 'active',
    settings JSONB DEFAULT '{}'::jsonb,
    working_days JSONB DEFAULT '["monday", "tuesday", "wednesday", "thursday", "friday"]'::jsonb,
    working_hours_start VARCHAR(10) DEFAULT '09:00',
    working_hours_end VARCHAR(10) DEFAULT '17:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_org_slug ON organizations (slug);

-- ─── 3. People Table ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    unique_id VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    profile_photo_url VARCHAR(500),
    department_id UUID,
    team_id UUID,
    designation_id UUID,
    category VARCHAR(50) DEFAULT 'employee',
    shift_id UUID,
    joining_date DATE,
    status person_status NOT NULL DEFAULT 'active',
    face_registered face_reg_status NOT NULL DEFAULT 'not_registered',
    custom_fields JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT uq_person_org_uid UNIQUE (organization_id, unique_id)
);

CREATE INDEX IF NOT EXISTS ix_person_org_name ON people (organization_id, full_name);
CREATE INDEX IF NOT EXISTS ix_person_org_dept ON people (organization_id, department_id);
CREATE INDEX IF NOT EXISTS ix_person_org_status ON people (organization_id, status);

-- ─── 4. Users Table (Authentication Accounts) ───────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    role user_role NOT NULL DEFAULT 'member',
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login TIMESTAMPTZ,
    person_id UUID REFERENCES people(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_user_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_user_org ON users (organization_id);

-- ─── 5. Departments Table ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    head_person_id UUID REFERENCES people(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT uq_dept_org_name UNIQUE (organization_id, name)
);

-- Foreign key link for people.department_id
ALTER TABLE people 
    DROP CONSTRAINT IF EXISTS fk_people_dept,
    ADD CONSTRAINT fk_people_dept FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL;

-- ─── 6. Teams Table ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT uq_team_org_name UNIQUE (organization_id, name)
);

ALTER TABLE people 
    DROP CONSTRAINT IF EXISTS fk_people_team,
    ADD CONSTRAINT fk_people_team FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL;

-- ─── 7. Designations Table ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS designations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    level INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT uq_desig_org_name UNIQUE (organization_id, name)
);

ALTER TABLE people 
    DROP CONSTRAINT IF EXISTS fk_people_desig,
    ADD CONSTRAINT fk_people_desig FOREIGN KEY (designation_id) REFERENCES designations(id) ON DELETE SET NULL;

-- ─── 8. Shifts Table ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS shifts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    start_time VARCHAR(10) NOT NULL,
    end_time VARCHAR(10) NOT NULL,
    grace_period_minutes INTEGER DEFAULT 15,
    is_overnight BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT uq_shift_org_name UNIQUE (organization_id, name)
);

ALTER TABLE people 
    DROP CONSTRAINT IF EXISTS fk_people_shift,
    ADD CONSTRAINT fk_people_shift FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE SET NULL;

-- ─── 9. Holidays Table ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS holidays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    is_optional BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT uq_holiday_org_date UNIQUE (organization_id, date)
);

-- ─── 10. Cameras Table ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    camera_type VARCHAR(50) DEFAULT 'webcam',
    stream_url VARCHAR(500),
    status camera_status NOT NULL DEFAULT 'offline',
    is_active BOOLEAN NOT NULL DEFAULT true,
    settings JSONB DEFAULT '{}'::jsonb,
    last_active TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT uq_camera_org_name UNIQUE (organization_id, name)
);

-- ─── 11. Face Profiles Table (128-d Vector Encodings) ───────────────────────

CREATE TABLE IF NOT EXISTS face_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL UNIQUE REFERENCES people(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    encoding BYTEA NOT NULL,
    image_url VARCHAR(500),
    quality_score DOUBLE PRECISION,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_face_org ON face_profiles (organization_id);

-- ─── 12. Face Registration Consents (GDPR Compliance) ──────────────────────

CREATE TABLE IF NOT EXISTS face_registration_consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    consent_given BOOLEAN NOT NULL DEFAULT false,
    consent_date TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    ip_address VARCHAR(50),
    withdrawn BOOLEAN DEFAULT false,
    withdrawn_date TIMESTAMPTZ
);

-- ─── 13. Attendance Sessions ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    session_date DATE NOT NULL,
    start_time VARCHAR(10),
    end_time VARCHAR(10),
    session_type VARCHAR(50) DEFAULT 'general',
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    shift_id UUID REFERENCES shifts(id) ON DELETE SET NULL,
    camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_session_org_date ON attendance_sessions (organization_id, session_date);

-- ─── 14. Attendance Records ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    session_id UUID REFERENCES attendance_sessions(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    status attendance_status NOT NULL DEFAULT 'present',
    action attendance_action,
    check_in_time TIMESTAMPTZ,
    check_out_time TIMESTAMPTZ,
    total_hours DOUBLE PRECISION,
    is_late BOOLEAN DEFAULT false,
    late_minutes INTEGER DEFAULT 0,
    is_early_departure BOOLEAN DEFAULT false,
    early_departure_minutes INTEGER DEFAULT 0,
    overtime_minutes INTEGER DEFAULT 0,
    camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
    recognition_confidence DOUBLE PRECISION,
    marked_by VARCHAR(50) DEFAULT 'ai',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_att_org_date ON attendance_records (organization_id, date);
CREATE INDEX IF NOT EXISTS ix_att_person_date ON attendance_records (person_id, date);
CREATE INDEX IF NOT EXISTS ix_att_org_person_date ON attendance_records (organization_id, person_id, date);

-- ─── 15. Attendance Corrections ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS attendance_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    attendance_record_id UUID NOT NULL REFERENCES attendance_records(id) ON DELETE CASCADE,
    requested_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_status attendance_status NOT NULL,
    requested_status attendance_status NOT NULL,
    original_check_in TIMESTAMPTZ,
    requested_check_in TIMESTAMPTZ,
    original_check_out TIMESTAMPTZ,
    requested_check_out TIMESTAMPTZ,
    reason TEXT NOT NULL,
    status correction_status NOT NULL DEFAULT 'pending',
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_corr_org_status ON attendance_corrections (organization_id, status);

-- ─── 16. Recognition Logs ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS recognition_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
    person_id UUID REFERENCES people(id) ON DELETE SET NULL,
    recognized BOOLEAN NOT NULL DEFAULT false,
    confidence DOUBLE PRECISION,
    faces_detected INTEGER DEFAULT 0,
    faces_recognized INTEGER DEFAULT 0,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_reclog_org_ts ON recognition_logs (organization_id, timestamp);

-- ─── 17. Notifications ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_notif_user_read ON notifications (user_id, is_read);

-- ─── 18. Audit Logs ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(50),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS ix_audit_org_ts ON audit_logs (organization_id, timestamp);

-- ─── 19. Subscription Plans ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    plan_type subscription_plan NOT NULL,
    max_people INTEGER DEFAULT 50,
    max_cameras INTEGER DEFAULT 2,
    max_admins INTEGER DEFAULT 2,
    price_monthly DOUBLE PRECISION DEFAULT 0.0,
    price_yearly DOUBLE PRECISION DEFAULT 0.0,
    features JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ─── 20. Organization Subscriptions ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS organization_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES subscription_plans(id) ON DELETE SET NULL,
    status subscription_status NOT NULL DEFAULT 'trial',
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ─── 21. Initial Seed Data ──────────────────────────────────────────────────

-- Default Subscription Tiers
INSERT INTO subscription_plans (name, plan_type, max_people, max_cameras, max_admins, price_monthly, price_yearly, features)
VALUES
    ('Free Tier', 'free', 25, 1, 1, 0.0, 0.0, '["Face Recognition", "Daily Attendance", "Webcam Support"]'::jsonb),
    ('Starter Plan', 'starter', 100, 3, 3, 49.0, 490.0, '["Face Recognition", "CSV/Excel Export", "Department Tracking", "Shift Management"]'::jsonb),
    ('Professional Plan', 'professional', 500, 10, 10, 149.0, 1490.0, '["RTSP Camera Streams", "Anti-Spoofing Liveness", "PDF Reports", "Audit Logs"]'::jsonb),
    ('Enterprise Plan', 'enterprise', 5000, 50, 50, 499.0, 4990.0, '["Unlimited Teams", "Custom Data Retention", "Priority Queue", "24/7 SLA Support"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Default Super Administrator (Password: Admin@12345)
-- bcrypt hash for 'Admin@12345': $2b$12$Z0.UeW7tN3i7GvV.zXk/8.tG5r2Xq4s0z3uL9p0q1r2s3t4u5v6w7
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES (
    'admin@attendora.com',
    '$2b$12$4O.bM7C7j9eL4m5W1d1d8.y/hS0J2S0Y5r6x5K2b5Y4e2S0v1u4Z6',
    'ATTENDORA Super Admin',
    'super_admin',
    true
)
ON CONFLICT (email) DO NOTHING;
