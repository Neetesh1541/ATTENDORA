import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Users,
  ScanFace,
  Video,
  Camera,
  CalendarCheck,
  BarChart3,
  FileSpreadsheet,
  Building2,
  Clock,
  FileEdit,
  Bell,
  Settings,
  ShieldAlert,
  CreditCard,
  History,
  Menu,
  X,
  Sun,
  Moon,
  LogOut,
  ChevronRight,
  Sparkles,
  Building,
} from 'lucide-react';
import { useAuth } from '../stores/authStore';
import { useTheme } from '../stores/themeStore';
import { notificationsApi } from '../services/api';
import Avatar from '../components/ui/Avatar';
import Badge from '../components/ui/Badge';
import Dropdown from '../components/ui/Dropdown';
import { cn } from '../utils/cn';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  adminOnly?: boolean;
  superAdminOnly?: boolean;
}

const mainNavItems: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'People', href: '/dashboard/people', icon: Users },
  { name: 'Face Registration', href: '/dashboard/face-registration', icon: ScanFace },
  { name: 'Live Recognition', href: '/dashboard/live-recognition', icon: Video, badge: 'Live' },
  { name: 'Cameras', href: '/dashboard/cameras', icon: Camera },
  { name: 'Attendance', href: '/dashboard/attendance', icon: CalendarCheck },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Reports', href: '/dashboard/reports', icon: FileSpreadsheet },
  { name: 'Departments & Teams', href: '/dashboard/departments', icon: Building2 },
  { name: 'Shifts & Schedules', href: '/dashboard/shifts', icon: Clock },
  { name: 'Corrections', href: '/dashboard/corrections', icon: FileEdit },
  { name: 'Notifications', href: '/dashboard/notifications', icon: Bell },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

const superAdminNavItems: NavItem[] = [
  { name: 'Organizations', href: '/dashboard/admin/organizations', icon: Building, superAdminOnly: true },
  { name: 'All Users', href: '/dashboard/admin/users', icon: Users, superAdminOnly: true },
  { name: 'Subscription Plans', href: '/dashboard/admin/plans', icon: CreditCard, superAdminOnly: true },
  { name: 'Audit Logs', href: '/dashboard/admin/audit-logs', icon: History, superAdminOnly: true },
];

export const DashboardLayout: React.FC = () => {
  const { user, organization, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const isSuperAdmin = user?.role === 'super_admin';

  useEffect(() => {
    // Fetch unread notifications count
    const fetchUnread = async () => {
      try {
        const res = await notificationsApi.unreadCount();
        setUnreadCount(res.unread_count);
      } catch {
        // fallback
      }
    };
    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Find active nav title for header breadcrumb
  const allNav = [...mainNavItems, ...superAdminNavItems];
  const activeNavItem = allNav.find((item) =>
    item.href === '/dashboard'
      ? location.pathname === '/dashboard'
      : location.pathname.startsWith(item.href)
  );

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar Component */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-200/80 bg-white shadow-xl transition-transform duration-300 ease-in-out dark:border-slate-800/80 dark:bg-slate-900 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo and Brand */}
        <div className="flex h-16 shrink-0 items-center justify-between px-6 border-b border-slate-100 dark:border-slate-800/80">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-700 to-brand-500 shadow-md shadow-brand-500/25 text-white">
              <ScanFace className="h-6 w-6" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                ATTENDORA
              </span>
              <span className="ml-1.5 rounded-md bg-brand-50 px-1.5 py-0.5 text-[10px] font-semibold text-brand-600 dark:bg-brand-950 dark:text-brand-400">
                AI SaaS
              </span>
            </div>
          </Link>

          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Organization Info Card */}
        {organization && (
          <div className="mx-4 mt-3 mb-1 rounded-xl bg-slate-50 p-3 border border-slate-100 dark:bg-slate-850 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700 dark:bg-brand-950 dark:text-brand-300 font-bold text-xs uppercase">
                {organization.name.slice(0, 2)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {organization.name}
                </p>
                <p className="truncate text-[10px] text-slate-500 dark:text-slate-400 capitalize">
                  {organization.org_type} • {organization.status}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation items list */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-6">
          <div>
            <p className="px-2 pb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Workspace
            </p>
            <nav className="space-y-1">
              {mainNavItems.map((item) => {
                const isActive =
                  item.href === '/dashboard'
                    ? location.pathname === '/dashboard'
                    : location.pathname.startsWith(item.href);

                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={cn(
                      'group flex items-center justify-between rounded-xl px-3 py-2 text-xs font-medium transition-all duration-150',
                      isActive
                        ? 'bg-brand-600 text-white font-semibold shadow-sm shadow-brand-500/20'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800/80 dark:hover:text-white'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon
                        className={cn(
                          'h-4 w-4 shrink-0 transition-colors',
                          isActive
                            ? 'text-white'
                            : 'text-slate-400 group-hover:text-slate-600 dark:text-slate-400 dark:group-hover:text-slate-200'
                        )}
                      />
                      <span>{item.name}</span>
                    </div>

                    {item.badge && (
                      <span
                        className={cn(
                          'rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider',
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400'
                        )}
                      >
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Super Admin section if applicable */}
          {isSuperAdmin && (
            <div>
              <p className="px-2 pb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                System Administration
              </p>
              <nav className="space-y-1">
                {superAdminNavItems.map((item) => {
                  const isActive = location.pathname.startsWith(item.href);
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={cn(
                        'group flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium transition-all duration-150',
                        isActive
                          ? 'bg-purple-600 text-white font-semibold shadow-sm'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800/80 dark:hover:text-white'
                      )}
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          )}
        </div>

        {/* Bottom User info & quick logout */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <Avatar
                src={user?.avatar_url}
                name={user?.full_name}
                size="sm"
                status="online"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {user?.full_name || 'User'}
                </p>
                <p className="truncate text-[10px] text-slate-500 dark:text-slate-400">
                  {user?.role?.replace('_', ' ')}
                </p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              title="Sign Out"
              className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400 transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Layout Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navbar */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200/80 bg-white px-4 sm:px-6 dark:border-slate-800/80 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>

            {/* Breadcrumb info */}
            <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-slate-400 dark:text-slate-500">
              <span>Attendora</span>
              <ChevronRight className="h-3.5 w-3.5" />
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {activeNavItem?.name || 'Dashboard'}
              </span>
            </div>
          </div>

          {/* Right Action Icons */}
          <div className="flex items-center gap-2.5 sm:gap-4">
            {/* Quick Live Mode Link */}
            <Link
              to="/dashboard/live-recognition"
              className="hidden md:inline-flex items-center gap-1.5 rounded-lg bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-100 dark:bg-brand-950/60 dark:text-brand-300 dark:hover:bg-brand-900 transition-colors"
            >
              <Sparkles className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
              <span>Launch Live AI</span>
            </Link>

            {/* Notifications Icon */}
            <Link
              to="/dashboard/notifications"
              className="relative rounded-xl p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
              title="Notifications"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-sm ring-2 ring-white dark:ring-slate-900">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>

            {/* Dark Mode Switcher */}
            <button
              onClick={toggleTheme}
              className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
              title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDark ? <Sun className="h-5 w-5 text-amber-400" /> : <Moon className="h-5 w-5" />}
            </button>

            {/* User Dropdown */}
            <Dropdown
              trigger={
                <div className="flex items-center gap-2 pl-2">
                  <Avatar
                    src={user?.avatar_url}
                    name={user?.full_name}
                    size="sm"
                  />
                  <div className="hidden text-left xl:block">
                    <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      {user?.full_name}
                    </p>
                    <p className="text-[10px] text-slate-400 capitalize">
                      {user?.role?.replace('_', ' ')}
                    </p>
                  </div>
                </div>
              }
              items={[
                {
                  label: 'My Profile & Settings',
                  icon: <Settings className="h-4 w-4" />,
                  onClick: () => navigate('/dashboard/settings'),
                },
                'divider',
                {
                  label: 'Sign Out',
                  icon: <LogOut className="h-4 w-4" />,
                  variant: 'danger',
                  onClick: handleLogout,
                },
              ]}
            />
          </div>
        </header>

        {/* Dynamic Route Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
