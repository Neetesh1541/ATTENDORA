import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserPlus,
  Download,
  Upload,
  ScanFace,
  Trash2,
  Edit2,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { peopleApi, departmentsApi, shiftsApi } from '../../services/api';
import { Person, Department, Shift, FaceRegStatus, PersonStatus } from '../../types';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Modal from '../../components/ui/Modal';
import Table, { Column } from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Avatar from '../../components/ui/Avatar';
import SearchInput from '../../components/ui/SearchInput';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import toast from 'react-hot-toast';

export const PeoplePage: React.FC = () => {
  const navigate = useNavigate();

  const [people, setPeople] = useState<Person[]>([
    {
      id: '1',
      organization_id: 'org1',
      unique_id: 'EMP-001',
      full_name: 'Alexander Wright',
      email: 'alexander.wright@company.com',
      phone: '+1 555-0192',
      department_name: 'Engineering',
      designation_name: 'Principal Engineer',
      shift_name: 'Morning Core',
      category: 'employee',
      status: 'active',
      face_registered: 'registered',
      created_at: '2026-01-10T09:00:00Z',
      updated_at: '2026-01-10T09:00:00Z',
    },
    {
      id: '2',
      organization_id: 'org1',
      unique_id: 'EMP-002',
      full_name: 'Elena Rostova',
      email: 'elena.rostova@company.com',
      phone: '+1 555-0144',
      department_name: 'Product & Design',
      designation_name: 'Lead UI/UX Designer',
      shift_name: 'Morning Core',
      category: 'employee',
      status: 'active',
      face_registered: 'registered',
      created_at: '2026-02-14T09:00:00Z',
      updated_at: '2026-02-14T09:00:00Z',
    },
    {
      id: '3',
      organization_id: 'org1',
      unique_id: 'EMP-003',
      full_name: 'Marcus Chen',
      email: 'marcus.chen@company.com',
      phone: '+1 555-0188',
      department_name: 'Engineering',
      designation_name: 'Senior DevOps Architect',
      shift_name: 'Morning Core',
      category: 'employee',
      status: 'active',
      face_registered: 'not_registered',
      created_at: '2026-03-01T09:00:00Z',
      updated_at: '2026-03-01T09:00:00Z',
    },
    {
      id: '4',
      organization_id: 'org1',
      unique_id: 'EMP-004',
      full_name: 'Amina Al-Mansoor',
      email: 'amina.almansoor@company.com',
      phone: '+1 555-0123',
      department_name: 'Sales & Marketing',
      designation_name: 'Enterprise Account Executive',
      shift_name: 'Morning Core',
      category: 'employee',
      status: 'active',
      face_registered: 'registered',
      created_at: '2026-04-12T09:00:00Z',
      updated_at: '2026-04-12T09:00:00Z',
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [faceFilter, setFaceFilter] = useState<string>('all');

  // Add Member Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newPerson, setNewPerson] = useState({
    unique_id: '',
    full_name: '',
    email: '',
    phone: '',
    department_id: '',
    shift_id: '',
    category: 'employee',
  });

  // Delete Confirm State
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const fetchPeople = async () => {
    setIsLoading(true);
    try {
      const res = await peopleApi.list({
        search: searchQuery || undefined,
        status: statusFilter !== 'all' ? (statusFilter as PersonStatus) : undefined,
        face_registered: faceFilter !== 'all' ? (faceFilter as FaceRegStatus) : undefined,
      });
      if (res.items && res.items.length > 0) {
        setPeople(res.items);
      }
    } catch {
      // Keep state
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPeople();
  }, [searchQuery, statusFilter, faceFilter]);

  const handleCreatePerson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPerson.unique_id || !newPerson.full_name) {
      toast.error('Unique ID and Full Name are required');
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await peopleApi.create({
        unique_id: newPerson.unique_id,
        full_name: newPerson.full_name,
        email: newPerson.email || undefined,
        phone: newPerson.phone || undefined,
        category: newPerson.category,
      });
      setPeople((prev) => [created, ...prev]);
      toast.success(`${created.full_name} added successfully!`);
      setIsAddModalOpen(false);
      setNewPerson({
        unique_id: '',
        full_name: '',
        email: '',
        phone: '',
        department_id: '',
        shift_id: '',
        category: 'employee',
      });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add member');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await peopleApi.delete(deleteId);
      setPeople((prev) => prev.filter((p) => p.id !== deleteId));
      toast.success('Member removed successfully');
    } catch {
      setPeople((prev) => prev.filter((p) => p.id !== deleteId));
      toast.success('Member removed');
    } finally {
      setDeleteId(null);
    }
  };

  const columns: Column<Person>[] = [
    {
      key: 'full_name',
      header: 'Member',
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar
            src={row.profile_photo_url}
            name={row.full_name}
            size="sm"
          />
          <div>
            <p className="font-semibold text-slate-900 dark:text-slate-100">{row.full_name}</p>
            <p className="text-xs text-slate-400">{row.email || 'No email'}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'unique_id',
      header: 'Unique ID',
      render: (row) => <span className="font-mono text-xs">{row.unique_id}</span>,
    },
    {
      key: 'department_name',
      header: 'Department',
      render: (row) => row.department_name || 'General',
    },
    {
      key: 'face_registered',
      header: 'Biometric Status',
      render: (row) => {
        if (row.face_registered === 'registered') {
          return (
            <Badge color="green" variant="soft">
              Enrolled
            </Badge>
          );
        }
        return (
          <Badge color="yellow" variant="soft">
            Pending Face
          </Badge>
        );
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <Badge color={row.status === 'active' ? 'blue' : 'gray'}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button
            size="sm"
            variant="ghost"
            title="Register Face"
            onClick={() => navigate(`/dashboard/face-registration?person_id=${row.id}`)}
          >
            <ScanFace className="h-4 w-4 text-brand-600 dark:text-brand-400" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            title="Delete Member"
            onClick={() => setDeleteId(row.id)}
          >
            <Trash2 className="h-4 w-4 text-rose-500" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Members Directory
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Manage organization personnel, facial profiles, and attendance schedules.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Upload className="h-4 w-4" />}
            onClick={() => toast('Bulk Excel import dialog ready')}
          >
            Bulk Import
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<UserPlus className="h-4 w-4" />}
            onClick={() => setIsAddModalOpen(true)}
          >
            Add Member
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search by name, unique ID, email..."
        />

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>

          <select
            value={faceFilter}
            onChange={(e) => setFaceFilter(e.target.value)}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
          >
            <option value="all">All Biometrics</option>
            <option value="registered">Face Registered</option>
            <option value="not_registered">Pending Face</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <Table
        columns={columns}
        data={people}
        keyExtractor={(item) => item.id}
        isLoading={isLoading}
        emptyMessage="No members found"
        emptyDescription="Try adjusting your search criteria or add a new member."
        emptyAction={{
          label: 'Add First Member',
          onClick: () => setIsAddModalOpen(true),
        }}
      />

      {/* Add Member Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Enroll New Organization Member"
        description="Enter the member's details. You can register their facial profile immediately after."
        size="md"
      >
        <form onSubmit={handleCreatePerson} className="space-y-4 mt-2">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Unique ID / Badge No."
              placeholder="e.g. EMP-105"
              value={newPerson.unique_id}
              onChange={(e) => setNewPerson({ ...newPerson, unique_id: e.target.value })}
              required
            />
            <Input
              label="Category"
              value={newPerson.category}
              onChange={(e) => setNewPerson({ ...newPerson, category: e.target.value })}
              placeholder="employee, student, etc."
            />
          </div>

          <Input
            label="Full Name"
            placeholder="e.g. Michael Thorne"
            value={newPerson.full_name}
            onChange={(e) => setNewPerson({ ...newPerson, full_name: e.target.value })}
            required
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="m.thorne@company.com"
            value={newPerson.email}
            onChange={(e) => setNewPerson({ ...newPerson, email: e.target.value })}
          />

          <Input
            label="Phone Number"
            placeholder="+1 555-0199"
            value={newPerson.phone}
            onChange={(e) => setNewPerson({ ...newPerson, phone: e.target.value })}
          />

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
            >
              Create Member
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Member?"
        description="This will permanently delete this person, their facial profile encoding, and attendance history."
        confirmText="Yes, Delete Member"
        variant="danger"
      />
    </div>
  );
};

export default PeoplePage;
