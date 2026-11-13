import React, { useState } from 'react';
import { Bell, CheckCheck, Clock, ShieldAlert, AlertTriangle, VideoOff, CheckCircle } from 'lucide-react';
import { Notification, NotificationType } from '../../types';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import toast from 'react-hot-toast';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: 'notif-1',
      organization_id: 'org1',
      type: 'late_arrival',
      title: 'Late Arrival Alert: Elena Rostova',
      message: 'Elena Rostova checked in 22 minutes after shift start time (Morning Core).',
      is_read: false,
      created_at: '2026-11-13T09:22:20Z',
    },
    {
      id: 'notif-2',
      organization_id: 'org1',
      type: 'correction_request',
      title: 'New Correction Request Pending Review',
      message: 'Marcus Chen submitted an excuse for absent status on Nov 13.',
      is_read: false,
      created_at: '2026-11-13T09:45:10Z',
    },
    {
      id: 'notif-3',
      organization_id: 'org1',
      type: 'camera_offline',
      title: 'Camera Terminal Warning',
      message: 'Camera 03 (Cafeteria & Breakroom) disconnected or stream interrupted.',
      is_read: true,
      created_at: '2026-11-12T18:00:15Z',
    },
  ]);

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    toast.success('All notifications marked as read');
  };

  const markRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
  };

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'late_arrival':
        return <Clock className="h-5 w-5 text-amber-500" />;
      case 'camera_offline':
        return <VideoOff className="h-5 w-5 text-rose-500" />;
      case 'correction_request':
        return <AlertTriangle className="h-5 w-5 text-brand-600" />;
      default:
        return <Bell className="h-5 w-5 text-slate-500" />;
    }
  };

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            System Notifications & Alerts
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Real-time triggers on shift tardiness, missing clock-outs, and vision hardware status.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={markAllRead}
          leftIcon={<CheckCheck className="h-4 w-4" />}
        >
          Mark All as Read
        </Button>
      </div>

      <div className="space-y-3">
        {notifications.map((n) => (
          <div
            key={n.id}
            onClick={() => markRead(n.id)}
            className={`flex items-start justify-between p-4 rounded-2xl border transition-all cursor-pointer ${
              !n.is_read
                ? 'border-brand-300/80 bg-brand-50/20 dark:border-brand-900/60 dark:bg-brand-950/20'
                : 'border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-900'
            }`}
          >
            <div className="flex items-start gap-3.5">
              <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800">
                {getIcon(n.type)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-xs text-slate-900 dark:text-white">
                    {n.title}
                  </h4>
                  {!n.is_read && (
                    <span className="h-2 w-2 rounded-full bg-brand-600 dark:bg-brand-400" />
                  )}
                </div>
                <p className="mt-1 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {n.message}
                </p>
                <span className="mt-2 block font-mono text-[10px] text-slate-400">
                  {new Date(n.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotificationsPage;
