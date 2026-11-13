import React, { useState } from 'react';
import { Building, ShieldCheck, Plus, CheckCircle, XCircle } from 'lucide-react';
import { Organization } from '../../../types';
import Table, { Column } from '../../../components/ui/Table';
import Badge from '../../../components/ui/Badge';
import Button from '../../../components/ui/Button';

export const AdminOrganizationsPage: React.FC = () => {
  const [orgs, setOrgs] = useState<Organization[]>([
    {
      id: 'org-1',
      name: 'Acme Technologies Global',
      slug: 'acme-tech',
      org_type: 'corporate',
      status: 'active',
      timezone: 'UTC',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'org-2',
      name: 'St. Jude Medical Institute',
      slug: 'st-jude-med',
      org_type: 'hospital',
      status: 'active',
      timezone: 'America/New_York',
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    },
    {
      id: 'org-3',
      name: 'Westside Metro Campus',
      slug: 'westside-metro',
      org_type: 'university',
      status: 'pending',
      timezone: 'America/Los_Angeles',
      created_at: '2026-03-10T00:00:00Z',
      updated_at: '2026-03-10T00:00:00Z',
    },
  ]);

  const columns: Column<Organization>[] = [
    {
      key: 'name',
      header: 'Organization',
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">{row.name}</p>
          <p className="text-xs text-slate-400 font-mono">/{row.slug}</p>
        </div>
      ),
    },
    {
      key: 'org_type',
      header: 'Industry / Type',
      render: (row) => <span className="capitalize">{row.org_type}</span>,
    },
    {
      key: 'timezone',
      header: 'Timezone',
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge color={row.status === 'active' ? 'green' : 'yellow'}>
          {row.status}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            All Tenant Organizations
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Super Administrator overview of all platform enterprise accounts.
          </p>
        </div>
      </div>

      <Table columns={columns} data={orgs} keyExtractor={(item) => item.id} />
    </div>
  );
};

export default AdminOrganizationsPage;
