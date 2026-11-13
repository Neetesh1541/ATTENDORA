import React, { useState } from 'react';
import { Building2, Plus, Users, Trash2, Edit2, ChevronRight } from 'lucide-react';
import { Department, Team } from '../../types';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Badge from '../../components/ui/Badge';
import toast from 'react-hot-toast';

export const DepartmentsPage: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([
    {
      id: 'd1',
      organization_id: 'org1',
      name: 'Engineering & DevOps',
      description: 'Core software development, architecture, and infrastructure reliability.',
      is_active: true,
      member_count: 52,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'd2',
      organization_id: 'org1',
      name: 'Product & Design',
      description: 'Product lifecycle, UX research, and UI design systems.',
      is_active: true,
      member_count: 24,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'd3',
      organization_id: 'org1',
      name: 'Operations & Facilities',
      description: 'Day-to-day facilities, logistics, and workplace management.',
      is_active: true,
      member_count: 36,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'd4',
      organization_id: 'org1',
      name: 'Sales & Customer Success',
      description: 'Enterprise revenue generation and client relationship management.',
      is_active: true,
      member_count: 36,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deptName, setDeptName] = useState('');
  const [deptDesc, setDeptDesc] = useState('');

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!deptName) return;

    const created: Department = {
      id: `d-${Date.now()}`,
      organization_id: 'org1',
      name: deptName,
      description: deptDesc,
      is_active: true,
      member_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setDepartments([...departments, created]);
    toast.success(`Department "${deptName}" created`);
    setIsModalOpen(false);
    setDeptName('');
    setDeptDesc('');
  };

  const handleDelete = (id: string) => {
    setDepartments((prev) => prev.filter((d) => d.id !== id));
    toast.success('Department deleted');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Departments & Organizational Units
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Group members into distinct business units and operational teams.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={() => setIsModalOpen(true)}
        >
          Add Department
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {departments.map((dept) => (
          <Card key={dept.id}>
            <Card.Content className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400">
                    <Building2 className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">
                      {dept.name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {dept.member_count} enrolled members
                    </p>
                  </div>
                </div>

                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleDelete(dept.id)}
                >
                  <Trash2 className="h-4 w-4 text-rose-500" />
                </Button>
              </div>

              {dept.description && (
                <p className="mt-3 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {dept.description}
                </p>
              )}
            </Card.Content>
          </Card>
        ))}
      </div>

      {/* Add Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Department"
        description="Create a organizational branch for roster management."
      >
        <form onSubmit={handleAdd} className="space-y-4 mt-2">
          <Input
            label="Department Name"
            placeholder="e.g. Quality Assurance"
            value={deptName}
            onChange={(e) => setDeptName(e.target.value)}
            required
          />

          <div className="space-y-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Description
            </label>
            <textarea
              rows={3}
              value={deptDesc}
              onChange={(e) => setDeptDesc(e.target.value)}
              placeholder="Responsibilities and purpose..."
              className="w-full rounded-xl border border-slate-300 bg-white p-3 text-xs text-slate-900 focus:border-brand-600 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Create Department
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default DepartmentsPage;
