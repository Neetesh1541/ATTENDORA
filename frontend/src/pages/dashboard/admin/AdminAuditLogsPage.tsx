import React, { useState } from 'react';
import { History, Shield, Search } from 'lucide-react';
import { AuditLog } from '../../../types';
import Table, { Column } from '../../../components/ui/Table';
import Badge from '../../../components/ui/Badge';

export const AdminAuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([
    {
      id: 'log-1',
      action: 'user_login',
      resource_type: 'User',
      resource_id: 'u-1',
      details: { email: 'admin@attendora.ai' },
      ip_address: '192.168.1.1',
      timestamp: '2026-11-13T09:00:15Z',
    },
    {
      id: 'log-2',
      action: 'face_registered',
      resource_type: 'Person',
      resource_id: 'p-1',
      details: { person_name: 'Alexander Wright', quality: 0.99 },
      ip_address: '192.168.1.10',
      timestamp: '2026-11-13T08:52:10Z',
    },
    {
      id: 'log-3',
      action: 'shift_created',
      resource_type: 'Shift',
      resource_id: 's-1',
      details: { name: 'Morning Core' },
      ip_address: '192.168.1.5',
      timestamp: '2026-11-12T14:30:00Z',
    },
  ]);

  const columns: Column<AuditLog>[] = [
    {
      key: 'action',
      header: 'Action Event',
      render: (row) => <Badge color="indigo">{row.action}</Badge>,
    },
    {
      key: 'resource_type',
      header: 'Resource',
      render: (row) => `${row.resource_type || '-'} (${row.resource_id || '-'})`,
    },
    {
      key: 'ip_address',
      header: 'Client IP',
      render: (row) => <span className="font-mono text-xs">{row.ip_address || '-'}</span>,
    },
    {
      key: 'timestamp',
      header: 'Timestamp',
      render: (row) => new Date(row.timestamp).toLocaleString(),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Security & Compliance Audit Trail
        </h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Immutable event log of administrative actions, biometric modifications, and auth sessions.
        </p>
      </div>

      <Table columns={columns} data={logs} keyExtractor={(item) => item.id} />
    </div>
  );
};

export default AdminAuditLogsPage;
