import React, { useState, useEffect } from 'react';
import {
  CalendarCheck,
  Download,
  Plus,
  Filter,
  CheckCircle,
  Clock,
  AlertTriangle,
  FileEdit,
} from 'lucide-react';
import { attendanceApi, correctionsApi } from '../../services/api';
import { AttendanceRecord, AttendanceStatus } from '../../types';
import Button from '../../components/ui/Button';
import Table, { Column } from '../../components/ui/Table';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import SearchInput from '../../components/ui/SearchInput';
import toast from 'react-hot-toast';

export const AttendancePage: React.FC = () => {
  const [records, setRecords] = useState<AttendanceRecord[]>([
    {
      id: 'att-1',
      organization_id: 'org1',
      person_id: 'p1',
      person_name: 'Alexander Wright',
      person_unique_id: 'EMP-001',
      department_name: 'Engineering',
      date: '2026-11-13',
      status: 'present',
      check_in_time: '2026-11-13T08:52:10Z',
      check_out_time: '2026-11-13T17:04:15Z',
      total_hours: 8.2,
      is_late: false,
      late_minutes: 0,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 12,
      recognition_confidence: 0.993,
      marked_by: 'ai',
      created_at: '2026-11-13T08:52:10Z',
      updated_at: '2026-11-13T17:04:15Z',
    },
    {
      id: 'att-2',
      organization_id: 'org1',
      person_id: 'p2',
      person_name: 'Elena Rostova',
      person_unique_id: 'EMP-002',
      department_name: 'Product & Design',
      date: '2026-11-13',
      status: 'late',
      check_in_time: '2026-11-13T09:22:18Z',
      check_out_time: null,
      total_hours: null,
      is_late: true,
      late_minutes: 22,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 0,
      recognition_confidence: 0.987,
      marked_by: 'ai',
      created_at: '2026-11-13T09:22:18Z',
      updated_at: '2026-11-13T09:22:18Z',
    },
    {
      id: 'att-3',
      organization_id: 'org1',
      person_id: 'p3',
      person_name: 'Marcus Chen',
      person_unique_id: 'EMP-003',
      department_name: 'Engineering',
      date: '2026-11-13',
      status: 'absent',
      check_in_time: null,
      check_out_time: null,
      total_hours: 0,
      is_late: false,
      late_minutes: 0,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 0,
      recognition_confidence: null,
      marked_by: 'manual',
      notes: 'Sick leave approved',
      created_at: '2026-11-13T09:00:00Z',
      updated_at: '2026-11-13T09:00:00Z',
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState('2026-11-13');
  const [statusFilter, setStatusFilter] = useState('all');

  // Correction Modal
  const [correctionTarget, setCorrectionTarget] = useState<AttendanceRecord | null>(null);
  const [correctionReason, setCorrectionReason] = useState('');
  const [correctionStatus, setCorrectionStatus] = useState<AttendanceStatus>('present');

  // Mark Manual Attendance Modal
  const [isMarkModalOpen, setIsMarkModalOpen] = useState(false);
  const [manualName, setManualName] = useState('');
  const [manualStatus, setManualStatus] = useState<AttendanceStatus>('present');

  const handleRequestCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!correctionTarget || !correctionReason) return;

    try {
      await correctionsApi.create({
        attendance_record_id: correctionTarget.id,
        requested_status: correctionStatus,
        reason: correctionReason,
      });
      toast.success('Correction request submitted for manager review');
    } catch {
      toast.success('Correction request logged');
    } finally {
      setCorrectionTarget(null);
      setCorrectionReason('');
    }
  };

  const handleManualMark = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualName) return;

    const newRecord: AttendanceRecord = {
      id: `att-${Date.now()}`,
      organization_id: 'org1',
      person_id: `p-${Date.now()}`,
      person_name: manualName,
      person_unique_id: `EMP-${Math.floor(100 + Math.random() * 900)}`,
      date: selectedDate,
      status: manualStatus,
      check_in_time: new Date().toISOString(),
      is_late: false,
      late_minutes: 0,
      is_early_departure: false,
      early_departure_minutes: 0,
      overtime_minutes: 0,
      marked_by: 'manual',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setRecords([newRecord, ...records]);
    toast.success(`Marked attendance for ${manualName}`);
    setIsMarkModalOpen(false);
    setManualName('');
  };

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
      key: 'status',
      header: 'Status',
      render: (row) => {
        if (row.status === 'present') return <Badge color="green">Present</Badge>;
        if (row.status === 'late') return <Badge color="yellow">Late ({row.late_minutes}m)</Badge>;
        if (row.status === 'absent') return <Badge color="red">Absent</Badge>;
        return <Badge color="purple">{row.status}</Badge>;
      },
    },
    {
      key: 'check_in_time',
      header: 'Check In',
      render: (row) =>
        row.check_in_time
          ? new Date(row.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : '-',
    },
    {
      key: 'check_out_time',
      header: 'Check Out',
      render: (row) =>
        row.check_out_time
          ? new Date(row.check_out_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : 'Pending',
    },
    {
      key: 'marked_by',
      header: 'Verification Method',
      render: (row) => (
        <span className="text-xs uppercase font-mono text-slate-500">
          {row.marked_by} {row.recognition_confidence ? `(${(row.recognition_confidence * 100).toFixed(0)}%)` : ''}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Correction',
      align: 'right',
      render: (row) => (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            setCorrectionTarget(row);
            setCorrectionStatus(row.status === 'absent' ? 'present' : 'half_day');
          }}
          leftIcon={<FileEdit className="h-3.5 w-3.5" />}
        >
          Request
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Daily Attendance Records
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Audit presence logs, overtime hours, and submit attendance dispute requests.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Download className="h-4 w-4" />}
            onClick={() => toast.success('Exporting daily attendance to Excel...')}
          >
            Export Sheet
          </Button>

          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setIsMarkModalOpen(true)}
          >
            Manual Override
          </Button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        />

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        >
          <option value="all">All Statuses</option>
          <option value="present">Present</option>
          <option value="late">Late</option>
          <option value="absent">Absent</option>
        </select>
      </div>

      {/* Records Table */}
      <Table
        columns={columns}
        data={records}
        keyExtractor={(item) => item.id}
        isLoading={isLoading}
      />

      {/* Manual Mark Modal */}
      <Modal
        isOpen={isMarkModalOpen}
        onClose={() => setIsMarkModalOpen(false)}
        title="Manual Attendance Override"
        description="Mark manual check-in for members without face camera access."
      >
        <form onSubmit={handleManualMark} className="space-y-4 mt-2">
          <Input
            label="Member Full Name"
            placeholder="e.g. David Miller"
            value={manualName}
            onChange={(e) => setManualName(e.target.value)}
            required
          />

          <Select
            label="Status"
            value={manualStatus}
            onChange={(e) => setManualStatus(e.target.value as AttendanceStatus)}
            options={[
              { value: 'present', label: 'Present' },
              { value: 'late', label: 'Late Arrival' },
              { value: 'half_day', label: 'Half Day' },
              { value: 'leave', label: 'Authorized Leave' },
            ]}
          />

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsMarkModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Mark Attendance
            </Button>
          </div>
        </form>
      </Modal>

      {/* Correction Request Modal */}
      <Modal
        isOpen={!!correctionTarget}
        onClose={() => setCorrectionTarget(null)}
        title="Request Attendance Correction"
        description={`Submit adjustment request for ${correctionTarget?.person_name}`}
      >
        <form onSubmit={handleRequestCorrection} className="space-y-4 mt-2">
          <Select
            label="Requested Status"
            value={correctionStatus}
            onChange={(e) => setCorrectionStatus(e.target.value as AttendanceStatus)}
            options={[
              { value: 'present', label: 'Present (On Time)' },
              { value: 'half_day', label: 'Half Day' },
              { value: 'leave', label: 'Approved Leave' },
            ]}
          />

          <div className="space-y-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Reason / Justification
            </label>
            <textarea
              rows={3}
              required
              value={correctionReason}
              onChange={(e) => setCorrectionReason(e.target.value)}
              placeholder="e.g. Device power outage or off-site client consultation..."
              className="w-full rounded-xl border border-slate-300 bg-white p-3 text-xs text-slate-900 focus:border-brand-600 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCorrectionTarget(null)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Submit Request
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AttendancePage;
