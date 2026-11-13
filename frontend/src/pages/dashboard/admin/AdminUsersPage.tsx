import React, { useState } from 'react';
import { Users, Shield, Plus } from 'lucide-react';
import { User } from '../../../types';
import Table, { Column } from '../../../components/ui/Table';
import Badge from '../../../components/ui/Badge';
import Avatar from '../../../components/ui/Avatar';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([
    {
      id: 'u1',
      full_name: 'Super Admin',
      email: 'admin@attendora.ai',
      role: 'super_admin',
      is_active: true,
      last_login: '2026-11-13T09:00:00Z',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'u2',
      full_name: 'Johnathan Acme',
      email: 'johnathan@acme.com',
      role: 'org_admin',
      is_active: true,
      last_login: '2026-11-13T08:45:00Z',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ]);

  const columns: Column<User>[] = [
    {
      key: 'full_name',
      header: 'User',
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar name={row.full_name} size="sm" />
          <div>
            <p className="font-semibold text-slate-900 dark:text-white">{row.full_name}</p>
            <p className="text-xs text-slate-400">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (row) => <Badge color="indigo">{row.role.replace('_', ' ')}</Badge>,
    },
    {
      key: 'is_active',
      header: 'Status',
      render: (row) => (
        <Badge color={row.is_active ? 'green' : 'red'}>
          {row.is_active ? 'Active' : 'Disabled'}
        </Badge>
      ),
    },
    {
      key: 'last_login',
      header: 'Last Login',
      render: (row) => (row.last_login ? new Date(row.last_login).toLocaleString() : 'Never'),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          System Users & IAM
        </h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Super Administrator access management across all tenant user credentials.
        </p>
      </div>

      <Table columns={columns} data={users} keyExtractor={(item) => item.id} />
    </div>
  );
};

export default AdminUsersPage;
