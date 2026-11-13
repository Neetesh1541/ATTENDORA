/**
 * ATTENDORA — TypeScript Domain & API Definitions
 * Matches backend FastAPI + SQLAlchemy models
 */

// ─── Enums ─────────────────────────────────────────────────────────────────

export type OrgStatus = 'active' | 'suspended' | 'deactivated' | 'pending';

export type UserRole = 'super_admin' | 'org_admin' | 'manager' | 'member';

export type PersonStatus = 'active' | 'inactive' | 'suspended';

export type FaceRegStatus = 'not_registered' | 'registered' | 'failed';

export type AttendanceStatus =
  | 'present'
  | 'absent'
  | 'late'
  | 'early_departure'
  | 'half_day'
  | 'leave'
  | 'holiday'
  | 'weekly_off';

export type AttendanceAction = 'check_in' | 'check_out' | 'break_start' | 'break_end';

export type CorrectionStatus = 'pending' | 'approved' | 'rejected';

export type CameraStatus = 'online' | 'offline' | 'error';

export type NotificationType =
  | 'attendance_marked'
  | 'late_arrival'
  | 'missing_checkout'
  | 'correction_request'
  | 'correction_approved'
  | 'correction_rejected'
  | 'camera_offline'
  | 'system_alert';

export type SubscriptionPlan = 'free' | 'starter' | 'professional' | 'enterprise';

export type SubscriptionStatus = 'active' | 'expired' | 'cancelled' | 'trial';

export type OrgType =
  | 'general'
  | 'corporate'
  | 'school'
  | 'university'
  | 'factory'
  | 'hospital'
  | 'retail'
  | 'gym'
  | 'other';

// ─── Core Models ───────────────────────────────────────────────────────────

export interface Organization {
  id: string;
  name: string;
  slug: string;
  org_type: OrgType | string;
  logo_url?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  zip_code?: string | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  status: OrgStatus;
  settings?: Record<string, any>;
  working_days?: string[];
  working_hours_start?: string;
  working_hours_end?: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  organization_id?: string | null;
  email: string;
  full_name: string;
  phone?: string | null;
  avatar_url?: string | null;
  role: UserRole;
  is_active: boolean;
  person_id?: string | null;
  last_login?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  head_person_id?: string | null;
  is_active: boolean;
  member_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Team {
  id: string;
  organization_id: string;
  department_id?: string | null;
  department_name?: string | null;
  name: string;
  description?: string | null;
  is_active: boolean;
  member_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Designation {
  id: string;
  organization_id: string;
  name: string;
  level: number;
  created_at: string;
}

export interface Shift {
  id: string;
  organization_id: string;
  name: string;
  start_time: string; // "09:00"
  end_time: string;   // "17:00"
  grace_period_minutes: number;
  is_overnight: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Holiday {
  id: string;
  organization_id: string;
  name: string;
  date: string; // YYYY-MM-DD
  is_optional: boolean;
  created_at: string;
}

export interface Person {
  id: string;
  organization_id: string;
  unique_id: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  profile_photo_url?: string | null;
  department_id?: string | null;
  department_name?: string | null;
  team_id?: string | null;
  team_name?: string | null;
  designation_id?: string | null;
  designation_name?: string | null;
  category: string;
  shift_id?: string | null;
  shift_name?: string | null;
  joining_date?: string | null;
  status: PersonStatus;
  face_registered: FaceRegStatus;
  custom_fields?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface FaceProfile {
  id: string;
  person_id: string;
  organization_id: string;
  image_url?: string | null;
  quality_score?: number | null;
  registered_at: string;
  updated_at: string;
}

export interface FaceRegistrationConsent {
  id: string;
  person_id: string;
  organization_id: string;
  consent_given: boolean;
  consent_date: string;
  ip_address?: string | null;
  withdrawn: boolean;
  withdrawn_date?: string | null;
}

export interface Camera {
  id: string;
  organization_id: string;
  name: string;
  location?: string | null;
  camera_type: 'webcam' | 'ip' | 'rtsp' | string;
  stream_url?: string | null;
  status: CameraStatus;
  is_active: boolean;
  settings?: Record<string, any>;
  last_active?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceSession {
  id: string;
  organization_id: string;
  name: string;
  session_date: string;
  start_time?: string | null;
  end_time?: string | null;
  session_type: string;
  department_id?: string | null;
  team_id?: string | null;
  shift_id?: string | null;
  camera_id?: string | null;
  is_active: boolean;
  created_by?: string | null;
  created_at: string;
  record_count?: number;
}

export interface AttendanceRecord {
  id: string;
  organization_id: string;
  person_id: string;
  person_name?: string | null;
  person_unique_id?: string | null;
  department_name?: string | null;
  session_id?: string | null;
  date: string;
  status: AttendanceStatus;
  action?: AttendanceAction | null;
  check_in_time?: string | null;
  check_out_time?: string | null;
  total_hours?: number | null;
  is_late: boolean;
  late_minutes: number;
  is_early_departure: boolean;
  early_departure_minutes: number;
  overtime_minutes: number;
  camera_id?: string | null;
  recognition_confidence?: number | null;
  marked_by: 'ai' | 'manual' | 'import' | string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceCorrection {
  id: string;
  organization_id: string;
  attendance_record_id: string;
  requested_by: string;
  requester_name?: string | null;
  person_name?: string | null;
  original_status: AttendanceStatus;
  requested_status: AttendanceStatus;
  original_check_in?: string | null;
  requested_check_in?: string | null;
  original_check_out?: string | null;
  requested_check_out?: string | null;
  reason: string;
  status: CorrectionStatus;
  reviewed_by?: string | null;
  review_notes?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface RecognitionResult {
  person_id: string | null;
  person_name?: string | null;
  person_unique_id?: string | null;
  confidence: number;
  box: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  matched: boolean;
  timestamp: string;
}

export interface RecognitionLog {
  id: string;
  organization_id: string;
  camera_id?: string | null;
  person_id?: string | null;
  recognized: boolean;
  confidence?: number | null;
  faces_detected: number;
  faces_recognized: number;
  timestamp: string;
}

export interface Notification {
  id: string;
  organization_id: string;
  user_id?: string | null;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  data?: Record<string, any>;
  created_at: string;
}

export interface AuditLog {
  id: string;
  organization_id?: string | null;
  user_id?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  details?: Record<string, any>;
  ip_address?: string | null;
  timestamp: string;
}

export interface SubscriptionPlanModel {
  id: string;
  name: string;
  plan_type: SubscriptionPlan;
  max_people: number;
  max_cameras: number;
  max_admins: number;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  is_active: boolean;
  created_at: string;
}

export interface OrganizationSubscription {
  id: string;
  organization_id: string;
  plan_id?: string | null;
  status: SubscriptionStatus;
  start_date: string;
  end_date?: string | null;
  plan?: SubscriptionPlanModel | null;
  created_at: string;
  updated_at: string;
}

// ─── API Request / Response Types ──────────────────────────────────────────

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  pages: number;
  items: T[];
}

export interface ListResponse<T> {
  total: number;
  items: T[];
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[];
}

export interface MessageResponse {
  message: string;
  detail?: string | null;
}

// ─── Auth Payloads ─────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  organization?: Organization | null;
}

export interface RegisterRequest {
  org_name: string;
  org_slug?: string;
  org_type: string;
  timezone?: string;
  admin_name: string;
  admin_email: string;
  admin_password: string;
  phone?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ProfileUpdateRequest {
  full_name?: string;
  phone?: string;
  avatar_url?: string;
}

// ─── Analytics & Stats Types ───────────────────────────────────────────────

export interface OrganizationStats {
  total_people: number;
  total_users: number;
  total_departments: number;
  total_cameras: number;
  total_active_shifts: number;
  today_present: number;
  today_absent: number;
  today_late: number;
  attendance_rate: number;
}

export interface AnalyticsOverview {
  total_members: number;
  present_today: number;
  absent_today: number;
  late_today: number;
  on_leave_today: number;
  attendance_percentage: number;
  active_cameras: number;
  total_cameras: number;
  pending_corrections: number;
}

export interface DailyTrendItem {
  date: string;
  present: number;
  absent: number;
  late: number;
  attendance_rate: number;
}

export interface AnalyticsTrends {
  trends: DailyTrendItem[];
}

export interface DepartmentAnalyticsItem {
  department_id?: string | null;
  department_name: string;
  total_members: number;
  present: number;
  absent: number;
  attendance_rate: number;
}

export interface ShiftAnalyticsItem {
  shift_id?: string | null;
  shift_name: string;
  total_assigned: number;
  on_time: number;
  late: number;
  absent: number;
}

export interface CameraAnalyticsItem {
  camera_id: string;
  camera_name: string;
  location?: string | null;
  status: CameraStatus;
  total_detections: number;
  total_recognized: number;
  accuracy_rate: number;
}

export interface AdminStats {
  total_organizations: number;
  active_organizations: number;
  total_users: number;
  total_people: number;
  total_attendance_today: number;
  total_cameras: number;
  active_subscriptions: number;
}

export interface TodaySummary {
  date: string;
  total_people: number;
  present: number;
  absent: number;
  late: number;
  half_day: number;
  on_leave: number;
  attendance_percentage: number;
  recent_records: AttendanceRecord[];
}

// ─── Filter & Form Inputs ──────────────────────────────────────────────────

export interface PersonFilterParams {
  department_id?: string;
  team_id?: string;
  shift_id?: string;
  status?: PersonStatus;
  face_registered?: FaceRegStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface AttendanceFilterParams {
  date?: string;
  start_date?: string;
  end_date?: string;
  department_id?: string;
  person_id?: string;
  status?: AttendanceStatus;
  session_id?: string;
  page?: number;
  page_size?: number;
}

export interface PersonCreateInput {
  unique_id: string;
  full_name: string;
  email?: string;
  phone?: string;
  profile_photo_url?: string;
  department_id?: string;
  team_id?: string;
  designation_id?: string;
  category?: string;
  shift_id?: string;
  joining_date?: string;
  status?: PersonStatus;
  custom_fields?: Record<string, any>;
}

export interface PersonUpdateInput extends Partial<PersonCreateInput> {
  face_registered?: FaceRegStatus;
}

export interface DepartmentInput {
  name: string;
  description?: string;
  head_person_id?: string;
  is_active?: boolean;
}

export interface TeamInput {
  name: string;
  department_id?: string;
  description?: string;
  is_active?: boolean;
}

export interface DesignationInput {
  name: string;
  level?: number;
}

export interface ShiftInput {
  name: string;
  start_time: string;
  end_time: string;
  grace_period_minutes?: number;
  is_overnight?: boolean;
  is_active?: boolean;
}

export interface HolidayInput {
  name: string;
  date: string;
  is_optional?: boolean;
}

export interface CameraInput {
  name: string;
  location?: string;
  camera_type?: string;
  stream_url?: string;
  is_active?: boolean;
  settings?: Record<string, any>;
}

export interface AttendanceCorrectionInput {
  attendance_record_id: string;
  requested_status: AttendanceStatus;
  requested_check_in?: string;
  requested_check_out?: string;
  reason: string;
}
