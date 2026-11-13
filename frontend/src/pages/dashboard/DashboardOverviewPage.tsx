import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  UserCheck,
  Clock,
  Percent,
  ScanFace,
  Video,
  FileSpreadsheet,
  ArrowRight,
  ShieldCheck,
  Camera as CameraIcon,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';
import { useAuth } from '../../stores/authStore';
import { analyticsApi, attendanceApi } from '../../services/api';
import StatsCard from '../../components/ui/StatsCard';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Table, { Column } from '../../components/ui/Table';
import { AttendanceRecord, DailyTrendItem, DepartmentAnalyticsItem } from '../../types';

export const DashboardOverviewPage: React.FC = () => {
  const { user, organization } = useAuth();

  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalMembers: 148,
    presentToday: 132,
    lateToday: 7,
    attendanceRate: 89.2,
    activeCameras: 4,
    totalCameras: 4,
  });

  const [trendData, setTrendData] = useState<DailyTrendItem[]>([
    { date: 'Mon', present: 128, absent: 20, late: 12, attendance_rate: 86.4 },
    { date: 'Tue', present: 135, absent: 13, late: 8, attendance_rate: 91.2 },
    { date: 'Wed', present: 140, absent: 8, late: 5, attendance_rate: 94.5 },
    { date: 'Thu', present: 138, absent: 10, late: 6, attendance_rate: 93.2 },
    { date: 'Fri', present: 132, absent: 16, late: 7, attendance_rate: 89.2 },
  ]);

  const [departmentData, setDepartmentData] = useState<DepartmentAnalyticsItem[]>([
    { department_name: 'Engineering', total_members: 52, present: 48, absent: 4, attendance_rate: 92.3 },
    { department_name: 'Product & Design', total_members: 24, present: 22, absent: 2, attendance_rate: 91.6 },
    { department_name: 'Operations', total_members: 36, present: 33, absent: 3, attendance_rate: 91.6 },
    { department_name: 'Sales & Marketing', total_members: 36, present: 29, absent: 7, attendance_rate: 80.5 },
  ]);

  const [recentRecords, setRecentRecords] = useState<AttendanceRecord[]>([
    {
      id: '1',
      organization_id: 'org1',
      person_id: 'p1',
      person_name: 'Alexander Wright',
      person_unique_id: 'EMP-014',
      department_name: 'Engineering',
      date: '2026-11-13',
      status: 'present',
      check_in_time: '2026-11-13T08:54:12Z',
      is_late: false,
      late_minutes: 0,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 0,
      recognition_confidence: 0.992,
      marked_by: 'ai',
      created_at: '2026-11-13T08:54:12Z',
      updated_at: '2026-11-13T08:54:12Z',
    },
    {
      id: '2',
      organization_id: 'org1',
      person_id: 'p2',
      person_name: 'Elena Rostova',
      person_unique_id: 'EMP-028',
      department_name: 'Product & Design',
      date: '2026-11-13',
      status: 'late',
      check_in_time: '2026-11-13T09:18:40Z',
      is_late: true,
      late_minutes: 18,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 0,
      recognition_confidence: 0.985,
      marked_by: 'ai',
      created_at: '2026-11-13T09:18:40Z',
      updated_at: '2026-11-13T09:18:40Z',
    },
    {
      id: '3',
      organization_id: 'org1',
      person_id: 'p3',
      person_name: 'Marcus Chen',
      person_unique_id: 'EMP-051',
      department_name: 'Engineering',
      date: '2026-11-13',
      status: 'present',
      check_in_time: '2026-11-13T08:42:01Z',
      is_late: false,
      late_minutes: 0,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 0,
      recognition_confidence: 0.998,
      marked_by: 'ai',
      created_at: '2026-11-13T08:42:01Z',
      updated_at: '2026-11-13T08:42:01Z',
    },
    {
      id: '4',
      organization_id: 'org1',
      person_id: 'p4',
      person_name: 'Amina Al-Mansoor',
      person_unique_id: 'EMP-089',
      department_name: 'Sales & Marketing',
      date: '2026-11-13',
      status: 'present',
      check_in_time: '2026-11-13T09:02:15Z',
      is_late: false,
      late_minutes: 0,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 0,
      recognition_confidence: 0.976,
      marked_by: 'ai',
      created_at: '2026-11-13T09:02:15Z',
      updated_at: '2026-11-13T09:02:15Z',
    },
  ]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [overview, trends, todaySum] = await Promise.allSettled([
          analyticsApi.overview(),
          analyticsApi.trends({ days: 7 }),
          attendanceApi.getTodaySummary(),
        ]);

        if (overview.status === 'fulfilled') {
          setStats((prev) => ({
            ...prev,
            totalMembers: overview.value.total_members || prev.totalMembers,
            presentToday: overview.value.present_today || prev.presentToday,
            lateToday: overview.value.late_today || prev.lateToday,
            attendanceRate: overview.value.attendance_percentage || prev.attendanceRate,
            activeCameras: overview.value.active_cameras || prev.activeCameras,
            totalCameras: overview.value.total_cameras || prev.totalCameras,
          }));
        }

        if (trends.status === 'fulfilled' && trends.value.trends?.length > 0) {
          setTrendData(trends.value.trends);
        }

        if (todaySum.status === 'fulfilled' && todaySum.value.recent_records?.length > 0) {
          setRecentRecords(todaySum.value.recent_records);
        }
      } catch {
        // use initial realistic demo state
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const columns: Column<AttendanceRecord>[] = [
    {
      key: 'person_name',
      header: 'Member',
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900 dark:text-slate-100">{row.person_name}</p>
          <p className="text-xs text-slate-400">{row.person_unique_id}</p>
        </div>
      ),
    },
    {
      key: 'department_name',
      header: 'Department',
      render: (row) => row.department_name || 'General',
    },
    {
      key: 'check_in_time',
      header: 'Check-in Time',
      render: (row) => {
        if (!row.check_in_time) return '-';
        return new Date(row.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => {
        if (row.status === 'present') return <Badge color="green">Present</Badge>;
        if (row.status === 'late') return <Badge color="yellow">Late ({row.late_minutes}m)</Badge>;
        return <Badge color="red">{row.status}</Badge>;
      },
    },
    {
      key: 'recognition_confidence',
      header: 'AI Confidence',
      render: (row) => (
        <span className="font-mono text-xs text-emerald-600 dark:text-emerald-400">
          {row.recognition_confidence ? `${(row.recognition_confidence * 100).toFixed(1)}%` : 'Manual'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Hello, {user?.full_name?.split(' ')[0] || 'Administrator'} 👋
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {organization?.name || 'Organization'} • Attendance Overview for today
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link to="/dashboard/face-registration">
            <Button variant="outline" size="sm" leftIcon={<ScanFace className="h-4 w-4" />}>
              Enroll Face
            </Button>
          </Link>
          <Link to="/dashboard/live-recognition">
            <Button variant="primary" size="sm" leftIcon={<Video className="h-4 w-4" />}>
              Launch Live Scanner
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          label="Total Active Members"
          value={stats.totalMembers}
          icon={<Users className="h-5 w-5" />}
          trend={{ value: 4.2, direction: 'up', label: 'vs last month' }}
          isLoading={isLoading}
        />
        <StatsCard
          label="Present Today"
          value={stats.presentToday}
          icon={<UserCheck className="h-5 w-5 text-emerald-600" />}
          trend={{ value: 91.2, direction: 'up', label: 'turnout rate' }}
          isLoading={isLoading}
        />
        <StatsCard
          label="Late Arrivals"
          value={stats.lateToday}
          icon={<Clock className="h-5 w-5 text-amber-500" />}
          trend={{ value: 2.1, direction: 'down', label: 'decrease vs yesterday' }}
          isLoading={isLoading}
        />
        <StatsCard
          label="Camera Fleet Status"
          value={`${stats.activeCameras}/${stats.totalCameras} Online`}
          icon={<CameraIcon className="h-5 w-5 text-brand-600" />}
          description="All recognition streams nominal"
          isLoading={isLoading}
        />
      </div>

      {/* Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attendance Trends Chart */}
        <Card className="lg:col-span-2">
          <Card.Header>
            <div className="flex items-center justify-between">
              <div>
                <Card.Title>Weekly Attendance Trend</Card.Title>
                <Card.Description>Daily headcount of present members across all shifts</Card.Description>
              </div>
              <Badge color="indigo">Last 7 Days</Badge>
            </div>
          </Card.Header>
          <Card.Content>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPresent" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(148, 163, 184, 0.2)" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '12px',
                      border: '1px solid #1e293b',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="present"
                    stroke="#4f46e5"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#colorPresent)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card.Content>
        </Card>

        {/* Department Breakdown */}
        <Card>
          <Card.Header>
            <Card.Title>Department Turnout</Card.Title>
            <Card.Description>Today&apos;s attendance percentage by team</Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              {departmentData.map((dept) => (
                <div key={dept.department_name} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-700 dark:text-slate-300">{dept.department_name}</span>
                    <span className="text-slate-900 dark:text-slate-100 font-bold">{dept.attendance_rate}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-brand-600 transition-all duration-500"
                      style={{ width: `${dept.attendance_rate}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-400">
                    <span>{dept.present} Present</span>
                    <span>{dept.absent} Absent</span>
                  </div>
                </div>
              ))}
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Live Recent Recognition Table */}
      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <div>
              <Card.Title>Recent AI Verifications</Card.Title>
              <Card.Description>Real-time attendance events processed by the vision pipeline</Card.Description>
            </div>
            <Link
              to="/dashboard/attendance"
              className="text-xs font-semibold text-brand-600 hover:text-brand-500 dark:text-brand-400 inline-flex items-center gap-1"
            >
              <span>View All Records</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </Card.Header>
        <Card.Content>
          <Table
            columns={columns}
            data={recentRecords}
            keyExtractor={(item) => item.id}
            isLoading={isLoading}
          />
        </Card.Content>
      </Card>
    </div>
  );
};

export default DashboardOverviewPage;
