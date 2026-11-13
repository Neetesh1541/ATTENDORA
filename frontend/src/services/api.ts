import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
  User,
  Organization,
  Department,
  Team,
  Designation,
  Person,
  Shift,
  Holiday,
  Camera,
  AttendanceSession,
  AttendanceRecord,
  AttendanceCorrection,
  FaceProfile,
  RecognitionResult,
  Notification,
  AuditLog,
  SubscriptionPlanModel,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  ChangePasswordRequest,
  ProfileUpdateRequest,
  OrganizationStats,
  AnalyticsOverview,
  AnalyticsTrends,
  DepartmentAnalyticsItem,
  ShiftAnalyticsItem,
  CameraAnalyticsItem,
  AdminStats,
  TodaySummary,
  PersonFilterParams,
  AttendanceFilterParams,
  PersonCreateInput,
  PersonUpdateInput,
  DepartmentInput,
  TeamInput,
  DesignationInput,
  ShiftInput,
  HolidayInput,
  CameraInput,
  AttendanceCorrectionInput,
  PaginatedResponse,
  ListResponse,
  MessageResponse,
  CameraStatus,
  AttendanceStatus,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Create base Axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('attendora_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401s and errors gracefully
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login if not already on auth page
      localStorage.removeItem('attendora_token');
      localStorage.removeItem('attendora_user');
      localStorage.removeItem('attendora_org');
      if (
        !window.location.pathname.startsWith('/login') &&
        !window.location.pathname.startsWith('/register') &&
        window.location.pathname !== '/'
      ) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ─── AUTH APIS ─────────────────────────────────────────────────────────────

export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>('/auth/login', credentials);
    return res.data;
  },

  register: async (payload: RegisterRequest): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>('/auth/register', payload);
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  updateProfile: async (data: ProfileUpdateRequest): Promise<User> => {
    const res = await apiClient.put<User>('/auth/profile', data);
    return res.data;
  },

  changePassword: async (data: ChangePasswordRequest): Promise<MessageResponse> => {
    const res = await apiClient.post<MessageResponse>('/auth/change-password', data);
    return res.data;
  },
};

// ─── ORGANIZATIONS APIS ─────────────────────────────────────────────────────

export const organizationsApi = {
  list: async (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<Organization>> => {
    const res = await apiClient.get<PaginatedResponse<Organization>>('/organizations', { params });
    return res.data;
  },

  get: async (id: string): Promise<Organization> => {
    const res = await apiClient.get<Organization>(`/organizations/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<Organization>): Promise<Organization> => {
    const res = await apiClient.put<Organization>(`/organizations/${id}`, data);
    return res.data;
  },

  getStats: async (id?: string): Promise<OrganizationStats> => {
    const endpoint = id ? `/organizations/${id}/stats` : '/organizations/stats';
    const res = await apiClient.get<OrganizationStats>(endpoint);
    return res.data;
  },
};

// ─── USERS APIS ────────────────────────────────────────────────────────────

export const usersApi = {
  list: async (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<User>> => {
    const res = await apiClient.get<PaginatedResponse<User>>('/users', { params });
    return res.data;
  },

  create: async (data: { email: string; full_name: string; password: string; role?: string; phone?: string }): Promise<User> => {
    const res = await apiClient.post<User>('/users', data);
    return res.data;
  },

  get: async (id: string): Promise<User> => {
    const res = await apiClient.get<User>(`/users/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<User & { password?: string }>): Promise<User> => {
    const res = await apiClient.put<User>(`/users/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/users/${id}`);
    return res.data;
  },
};

// ─── DEPARTMENTS APIS ──────────────────────────────────────────────────────

export const departmentsApi = {
  list: async (): Promise<ListResponse<Department>> => {
    const res = await apiClient.get<ListResponse<Department>>('/departments');
    return res.data;
  },

  create: async (data: DepartmentInput): Promise<Department> => {
    const res = await apiClient.post<Department>('/departments', data);
    return res.data;
  },

  get: async (id: string): Promise<Department> => {
    const res = await apiClient.get<Department>(`/departments/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<DepartmentInput>): Promise<Department> => {
    const res = await apiClient.put<Department>(`/departments/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/departments/${id}`);
    return res.data;
  },
};

// ─── TEAMS APIS ─────────────────────────────────────────────────────────────

export const teamsApi = {
  list: async (departmentId?: string): Promise<ListResponse<Team>> => {
    const res = await apiClient.get<ListResponse<Team>>('/teams', {
      params: departmentId ? { department_id: departmentId } : undefined,
    });
    return res.data;
  },

  create: async (data: TeamInput): Promise<Team> => {
    const res = await apiClient.post<Team>('/teams', data);
    return res.data;
  },

  get: async (id: string): Promise<Team> => {
    const res = await apiClient.get<Team>(`/teams/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<TeamInput>): Promise<Team> => {
    const res = await apiClient.put<Team>(`/teams/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/teams/${id}`);
    return res.data;
  },
};

// ─── DESIGNATIONS APIS ──────────────────────────────────────────────────────

export const designationsApi = {
  list: async (): Promise<ListResponse<Designation>> => {
    const res = await apiClient.get<ListResponse<Designation>>('/designations');
    return res.data;
  },

  create: async (data: DesignationInput): Promise<Designation> => {
    const res = await apiClient.post<Designation>('/designations', data);
    return res.data;
  },

  get: async (id: string): Promise<Designation> => {
    const res = await apiClient.get<Designation>(`/designations/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<DesignationInput>): Promise<Designation> => {
    const res = await apiClient.put<Designation>(`/designations/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/designations/${id}`);
    return res.data;
  },
};

// ─── PEOPLE APIS ───────────────────────────────────────────────────────────

export const peopleApi = {
  list: async (params?: PersonFilterParams): Promise<PaginatedResponse<Person>> => {
    const res = await apiClient.get<PaginatedResponse<Person>>('/people', { params });
    return res.data;
  },

  get: async (id: string): Promise<Person> => {
    const res = await apiClient.get<Person>(`/people/${id}`);
    return res.data;
  },

  create: async (data: PersonCreateInput): Promise<Person> => {
    const res = await apiClient.post<Person>('/people', data);
    return res.data;
  },

  update: async (id: string, data: PersonUpdateInput): Promise<Person> => {
    const res = await apiClient.put<Person>(`/people/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/people/${id}`);
    return res.data;
  },

  bulkImport: async (people: Array<Record<string, any>>): Promise<{ imported: number; failed: number; errors: string[] }> => {
    const res = await apiClient.post('/people/import', { people });
    return res.data;
  },

  exportCsvUrl: (params?: PersonFilterParams): string => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return `${API_BASE_URL}/people/export?${query}`;
  },
};

// ─── SHIFTS APIS ────────────────────────────────────────────────────────────

export const shiftsApi = {
  list: async (): Promise<ListResponse<Shift>> => {
    const res = await apiClient.get<ListResponse<Shift>>('/shifts');
    return res.data;
  },

  create: async (data: ShiftInput): Promise<Shift> => {
    const res = await apiClient.post<Shift>('/shifts', data);
    return res.data;
  },

  get: async (id: string): Promise<Shift> => {
    const res = await apiClient.get<Shift>(`/shifts/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<ShiftInput>): Promise<Shift> => {
    const res = await apiClient.put<Shift>(`/shifts/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/shifts/${id}`);
    return res.data;
  },
};

// ─── HOLIDAYS APIS ─────────────────────────────────────────────────────────

export const holidaysApi = {
  list: async (params?: { year?: number }): Promise<ListResponse<Holiday>> => {
    const res = await apiClient.get<ListResponse<Holiday>>('/holidays', { params });
    return res.data;
  },

  create: async (data: HolidayInput): Promise<Holiday> => {
    const res = await apiClient.post<Holiday>('/holidays', data);
    return res.data;
  },

  get: async (id: string): Promise<Holiday> => {
    const res = await apiClient.get<Holiday>(`/holidays/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<HolidayInput>): Promise<Holiday> => {
    const res = await apiClient.put<Holiday>(`/holidays/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/holidays/${id}`);
    return res.data;
  },
};

// ─── CAMERAS APIS ──────────────────────────────────────────────────────────

export const camerasApi = {
  list: async (): Promise<ListResponse<Camera>> => {
    const res = await apiClient.get<ListResponse<Camera>>('/cameras');
    return res.data;
  },

  create: async (data: CameraInput): Promise<Camera> => {
    const res = await apiClient.post<Camera>('/cameras', data);
    return res.data;
  },

  get: async (id: string): Promise<Camera> => {
    const res = await apiClient.get<Camera>(`/cameras/${id}`);
    return res.data;
  },

  update: async (id: string, data: Partial<CameraInput>): Promise<Camera> => {
    const res = await apiClient.put<Camera>(`/cameras/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/cameras/${id}`);
    return res.data;
  },

  updateStatus: async (id: string, status: CameraStatus): Promise<Camera> => {
    const res = await apiClient.patch<Camera>(`/cameras/${id}/status`, { status });
    return res.data;
  },
};

// ─── FACES APIS ────────────────────────────────────────────────────────────

export const facesApi = {
  register: async (personId: string, imageFileOrBase64: File | string, consent = true): Promise<FaceProfile> => {
    const formData = new FormData();
    formData.append('person_id', personId);
    formData.append('consent_given', String(consent));

    if (imageFileOrBase64 instanceof File) {
      formData.append('image', imageFileOrBase64);
    } else {
      formData.append('image_base64', imageFileOrBase64);
    }

    const res = await apiClient.post<FaceProfile>('/faces/register', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  update: async (personId: string, imageFileOrBase64: File | string): Promise<FaceProfile> => {
    const formData = new FormData();
    if (imageFileOrBase64 instanceof File) {
      formData.append('image', imageFileOrBase64);
    } else {
      formData.append('image_base64', imageFileOrBase64);
    }

    const res = await apiClient.put<FaceProfile>(`/faces/${personId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  delete: async (personId: string): Promise<MessageResponse> => {
    const res = await apiClient.delete<MessageResponse>(`/faces/${personId}`);
    return res.data;
  },

  getStatus: async (personId: string): Promise<{ registered: boolean; profile?: FaceProfile | null }> => {
    const res = await apiClient.get(`/faces/${personId}/status`);
    return res.data;
  },

  verify: async (imageBase64: string, cameraId?: string): Promise<RecognitionResult[]> => {
    const res = await apiClient.post<RecognitionResult[]>('/faces/verify', {
      image_base64: imageBase64,
      camera_id: cameraId,
    });
    return res.data;
  },
};

// ─── ATTENDANCE APIS ───────────────────────────────────────────────────────

export const attendanceApi = {
  createSession: async (data: Partial<AttendanceSession>): Promise<AttendanceSession> => {
    const res = await apiClient.post<AttendanceSession>('/attendance/sessions', data);
    return res.data;
  },

  listSessions: async (params?: { date?: string; page?: number }): Promise<PaginatedResponse<AttendanceSession>> => {
    const res = await apiClient.get<PaginatedResponse<AttendanceSession>>('/attendance/sessions', { params });
    return res.data;
  },

  markAttendance: async (data: {
    person_id: string;
    date: string;
    status: AttendanceStatus;
    session_id?: string;
    check_in_time?: string;
    check_out_time?: string;
    notes?: string;
  }): Promise<AttendanceRecord> => {
    const res = await apiClient.post<AttendanceRecord>('/attendance/mark', data);
    return res.data;
  },

  getRecords: async (params?: AttendanceFilterParams): Promise<PaginatedResponse<AttendanceRecord>> => {
    const res = await apiClient.get<PaginatedResponse<AttendanceRecord>>('/attendance/records', { params });
    return res.data;
  },

  getTodaySummary: async (): Promise<TodaySummary> => {
    const res = await apiClient.get<TodaySummary>('/attendance/today-summary');
    return res.data;
  },

  checkIn: async (data: { person_id: string; camera_id?: string; check_in_time?: string; notes?: string }): Promise<AttendanceRecord> => {
    const res = await apiClient.post<AttendanceRecord>('/attendance/check-in', data);
    return res.data;
  },

  checkOut: async (data: { person_id: string; camera_id?: string; check_out_time?: string; notes?: string }): Promise<AttendanceRecord> => {
    const res = await apiClient.post<AttendanceRecord>('/attendance/check-out', data);
    return res.data;
  },
};

// ─── CORRECTIONS APIS ──────────────────────────────────────────────────────

export const correctionsApi = {
  create: async (data: AttendanceCorrectionInput): Promise<AttendanceCorrection> => {
    const res = await apiClient.post<AttendanceCorrection>('/corrections', data);
    return res.data;
  },

  list: async (params?: { status?: string; page?: number }): Promise<PaginatedResponse<AttendanceCorrection>> => {
    const res = await apiClient.get<PaginatedResponse<AttendanceCorrection>>('/corrections', { params });
    return res.data;
  },

  get: async (id: string): Promise<AttendanceCorrection> => {
    const res = await apiClient.get<AttendanceCorrection>(`/corrections/${id}`);
    return res.data;
  },

  approve: async (id: string, notes?: string): Promise<AttendanceCorrection> => {
    const res = await apiClient.post<AttendanceCorrection>(`/corrections/${id}/approve`, { review_notes: notes });
    return res.data;
  },

  reject: async (id: string, notes?: string): Promise<AttendanceCorrection> => {
    const res = await apiClient.post<AttendanceCorrection>(`/corrections/${id}/reject`, { review_notes: notes });
    return res.data;
  },
};

// ─── ANALYTICS APIS ────────────────────────────────────────────────────────

export const analyticsApi = {
  overview: async (params?: { date?: string }): Promise<AnalyticsOverview> => {
    const res = await apiClient.get<AnalyticsOverview>('/analytics/overview', { params });
    return res.data;
  },

  trends: async (params?: { days?: number }): Promise<AnalyticsTrends> => {
    const res = await apiClient.get<AnalyticsTrends>('/analytics/trends', { params });
    return res.data;
  },

  departmentWise: async (params?: { date?: string }): Promise<DepartmentAnalyticsItem[]> => {
    const res = await apiClient.get<DepartmentAnalyticsItem[]>('/analytics/departments', { params });
    return res.data;
  },

  shiftWise: async (params?: { date?: string }): Promise<ShiftAnalyticsItem[]> => {
    const res = await apiClient.get<ShiftAnalyticsItem[]>('/analytics/shifts', { params });
    return res.data;
  },

  cameraWise: async (): Promise<CameraAnalyticsItem[]> => {
    const res = await apiClient.get<CameraAnalyticsItem[]>('/analytics/cameras');
    return res.data;
  },
};

// ─── REPORTS APIS ──────────────────────────────────────────────────────────

export const reportsApi = {
  daily: async (params: { date: string; department_id?: string }) => {
    const res = await apiClient.get('/reports/daily', { params });
    return res.data;
  },

  monthly: async (params: { year: number; month: number; department_id?: string }) => {
    const res = await apiClient.get('/reports/monthly', { params });
    return res.data;
  },

  custom: async (params: { start_date: string; end_date: string; department_id?: string }) => {
    const res = await apiClient.get('/reports/custom', { params });
    return res.data;
  },

  exportExcel: async (params: Record<string, any>): Promise<Blob> => {
    const res = await apiClient.get('/reports/export/excel', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  exportCsv: async (params: Record<string, any>): Promise<Blob> => {
    const res = await apiClient.get('/reports/export/csv', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  exportPdf: async (params: Record<string, any>): Promise<Blob> => {
    const res = await apiClient.get('/reports/export/pdf', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },
};

// ─── NOTIFICATIONS APIS ────────────────────────────────────────────────────

export const notificationsApi = {
  list: async (params?: { page?: number; is_read?: boolean }): Promise<PaginatedResponse<Notification>> => {
    const res = await apiClient.get<PaginatedResponse<Notification>>('/notifications', { params });
    return res.data;
  },

  markRead: async (id: string): Promise<Notification> => {
    const res = await apiClient.patch<Notification>(`/notifications/${id}/read`);
    return res.data;
  },

  markAllRead: async (): Promise<MessageResponse> => {
    const res = await apiClient.post<MessageResponse>('/notifications/mark-all-read');
    return res.data;
  },

  unreadCount: async (): Promise<{ unread_count: number }> => {
    const res = await apiClient.get<{ unread_count: number }>('/notifications/unread-count');
    return res.data;
  },
};

// ─── ADMIN APIS ────────────────────────────────────────────────────────────

export const adminApi = {
  stats: async (): Promise<AdminStats> => {
    const res = await apiClient.get<AdminStats>('/admin/stats');
    return res.data;
  },

  organizations: async (params?: { page?: number; search?: string }): Promise<PaginatedResponse<Organization>> => {
    const res = await apiClient.get<PaginatedResponse<Organization>>('/admin/organizations', { params });
    return res.data;
  },

  auditLogs: async (params?: { page?: number; action?: string }): Promise<PaginatedResponse<AuditLog>> => {
    const res = await apiClient.get<PaginatedResponse<AuditLog>>('/admin/audit-logs', { params });
    return res.data;
  },

  plans: async (): Promise<ListResponse<SubscriptionPlanModel>> => {
    const res = await apiClient.get<ListResponse<SubscriptionPlanModel>>('/admin/plans');
    return res.data;
  },

  createPlan: async (data: Partial<SubscriptionPlanModel>): Promise<SubscriptionPlanModel> => {
    const res = await apiClient.post<SubscriptionPlanModel>('/admin/plans', data);
    return res.data;
  },

  updatePlan: async (id: string, data: Partial<SubscriptionPlanModel>): Promise<SubscriptionPlanModel> => {
    const res = await apiClient.put<SubscriptionPlanModel>(`/admin/plans/${id}`, data);
    return res.data;
  },
};

export default apiClient;
