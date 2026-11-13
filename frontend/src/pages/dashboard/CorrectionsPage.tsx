import React, { useState } from 'react';
import { FileEdit, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { AttendanceCorrection } from '../../types';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Table, { Column } from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import toast from 'react-hot-toast';

export const CorrectionsPage: React.FC = () => {
  const [corrections, setCorrections] = useState<AttendanceCorrection[]>([
    {
      id: 'corr-1',
      organization_id: 'org1',
      attendance_record_id: 'att-2',
      requested_by: 'u1',
      requester_name: 'Elena Rostova',
      person_name: 'Elena Rostova',
      original_status: 'late',
      requested_status: 'present',
      reason: 'Delayed at reception visitor gate due to badge security sensor calibration.',
      status: 'pending',
      created_at: '2026-11-13T09:30:00Z',
    },
    {
      id: 'corr-2',
      organization_id: 'org1',
      attendance_record_id: 'att-3',
      requested_by: 'u2',
      requester_name: 'Alexander Wright',
      person_name: 'Marcus Chen',
      original_status: 'absent',
      requested_status: 'present',
      reason: 'On-site emergency client server outage diagnosis approved by manager.',
      status: 'pending',
      created_at: '2026-11-13T09:45:00Z',
    },
  ]);

  const [reviewId, setReviewId] = useState<string | null>(null);
  const [reviewAction, setReviewAction] = useState<'approved' | 'rejected'>('approved');
  const [reviewNotes, setReviewNotes] = useState('');

  const handleReviewSubmit = () => {
    if (!reviewId) return;

    setCorrections((prev) =>
      prev.map((c) =>
        c.id === reviewId
          ? {
              ...c,
              status: reviewAction,
              review_notes: reviewNotes,
              reviewed_at: new Date().toISOString(),
            }
          : c
      )
    );

    toast.success(`Correction request ${reviewAction}`);
    setReviewId(null);
    setReviewNotes('');
  };

  const columns: Column<AttendanceCorrection>[] = [
    {
      key: 'person_name',
      header: 'Member',
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">{row.person_name}</p>
          <p className="text-[11px] text-slate-400">By: {row.requester_name}</p>
        </div>
      ),
    },
    {
      key: 'requested_status',
      header: 'Requested Change',
      render: (row) => (
        <div className="flex items-center gap-1.5 text-xs font-medium">
          <span className="line-through text-slate-400 capitalize">{row.original_status}</span>
          <span>→</span>
          <span className="text-brand-600 dark:text-brand-400 capitalize font-bold">
            {row.requested_status}
          </span>
        </div>
      ),
    },
    {
      key: 'reason',
      header: 'Reason',
      render: (row) => (
        <p className="max-w-xs truncate text-xs text-slate-600 dark:text-slate-300" title={row.reason}>
          {row.reason}
        </p>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => {
        if (row.status === 'approved') return <Badge color="green">Approved</Badge>;
        if (row.status === 'rejected') return <Badge color="red">Rejected</Badge>;
        return <Badge color="yellow">Pending Review</Badge>;
      },
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (row) =>
        row.status === 'pending' ? (
          <div className="flex items-center justify-end gap-1.5">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setReviewId(row.id);
                setReviewAction('approved');
              }}
            >
              Approve
            </Button>
            <Button
              size="sm"
              variant="danger"
              onClick={() => {
                setReviewId(row.id);
                setReviewAction('rejected');
              }}
            >
              Reject
            </Button>
          </div>
        ) : (
          <span className="text-xs text-slate-400">Reviewed</span>
        ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Attendance Corrections & Dispute Workflow
        </h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Review employee attendance change requests, missed check-in appeals, and excuses.
        </p>
      </div>

      <Table
        columns={columns}
        data={corrections}
        keyExtractor={(item) => item.id}
        emptyMessage="No pending correction requests"
        emptyDescription="All attendance disputes have been reviewed."
      />

      {/* Review Modal */}
      <Modal
        isOpen={!!reviewId}
        onClose={() => setReviewId(null)}
        title={`${reviewAction === 'approved' ? 'Approve' : 'Reject'} Attendance Correction`}
        description="Provide optional reviewer remarks for this attendance audit adjustment."
      >
        <div className="space-y-4 mt-2">
          <div className="space-y-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Audit Remarks
            </label>
            <textarea
              rows={3}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="e.g. Verified with security logs..."
              className="w-full rounded-xl border border-slate-300 bg-white p-3 text-xs text-slate-900 focus:border-brand-600 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" onClick={() => setReviewId(null)}>
              Cancel
            </Button>
            <Button
              variant={reviewAction === 'approved' ? 'primary' : 'danger'}
              onClick={handleReviewSubmit}
            >
              Confirm {reviewAction === 'approved' ? 'Approval' : 'Rejection'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default CorrectionsPage;
