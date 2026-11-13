import React, { useState } from 'react';
import { Clock, Plus, Calendar, Moon, Sun, Trash2, Edit2 } from 'lucide-react';
import { Shift, Holiday } from '../../types';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Badge from '../../components/ui/Badge';
import Tabs from '../../components/ui/Tabs';
import toast from 'react-hot-toast';

export const ShiftsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'shifts' | 'holidays'>('shifts');

  const [shifts, setShifts] = useState<Shift[]>([
    {
      id: 's1',
      organization_id: 'org1',
      name: 'Standard Morning Core',
      start_time: '09:00',
      end_time: '17:00',
      grace_period_minutes: 15,
      is_overnight: false,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 's2',
      organization_id: 'org1',
      name: 'Afternoon Flexi',
      start_time: '13:00',
      end_time: '21:00',
      grace_period_minutes: 20,
      is_overnight: false,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 's3',
      organization_id: 'org1',
      name: 'Overnight Ops',
      start_time: '21:00',
      end_time: '05:00',
      grace_period_minutes: 10,
      is_overnight: true,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
  ]);

  const [holidays, setHolidays] = useState<Holiday[]>([
    { id: 'h1', organization_id: 'org1', name: "New Year's Day", date: '2026-01-01', is_optional: false, created_at: '' },
    { id: 'h2', organization_id: 'org1', name: 'Spring Equinox Holiday', date: '2026-03-21', is_optional: false, created_at: '' },
    { id: 'h3', organization_id: 'org1', name: 'Annual Company Day', date: '2026-06-15', is_optional: true, created_at: '' },
  ]);

  const [isShiftModalOpen, setIsShiftModalOpen] = useState(false);
  const [newShift, setNewShift] = useState({
    name: '',
    start_time: '09:00',
    end_time: '17:00',
    grace_period_minutes: 15,
    is_overnight: false,
  });

  const handleAddShift = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newShift.name) return;

    const created: Shift = {
      id: `s-${Date.now()}`,
      organization_id: 'org1',
      ...newShift,
      is_active: true,
      created_at: new Date().toISOString(),
    };

    setShifts([...shifts, created]);
    toast.success(`Shift "${created.name}" created`);
    setIsShiftModalOpen(false);
    setNewShift({ name: '', start_time: '09:00', end_time: '17:00', grace_period_minutes: 15, is_overnight: false });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Shifts & Holiday Schedules
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Define daily operating windows, grace periods, and calendar holidays.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={() => setIsShiftModalOpen(true)}
        >
          Create Shift Schedule
        </Button>
      </div>

      <Tabs
        tabs={[
          { id: 'shifts', label: 'Work Shifts', icon: <Clock className="h-4 w-4" /> },
          { id: 'holidays', label: 'Official Holidays', icon: <Calendar className="h-4 w-4" /> },
        ]}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as any)}
      />

      {activeTab === 'shifts' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {shifts.map((shift) => (
            <Card key={shift.id}>
              <Card.Content className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400">
                      {shift.is_overnight ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-white">
                        {shift.name}
                      </h3>
                      {shift.is_overnight && (
                        <span className="text-[10px] text-amber-500 font-semibold">Overnight Shift</span>
                      )}
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setShifts(shifts.filter((s) => s.id !== shift.id));
                      toast.success('Shift removed');
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-rose-500" />
                  </Button>
                </div>

                <div className="mt-4 flex items-center justify-between text-xs border-y border-slate-100 dark:border-slate-800 py-3">
                  <div>
                    <span className="text-slate-400">Time Window:</span>
                    <p className="font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                      {shift.start_time} — {shift.end_time}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400">Grace Allowance:</span>
                    <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                      {shift.grace_period_minutes} mins
                    </p>
                  </div>
                </div>
              </Card.Content>
            </Card>
          ))}
        </div>
      ) : (
        <div className="max-w-2xl space-y-3">
          {holidays.map((hol) => (
            <div
              key={hol.id}
              className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-brand-600" />
                <div>
                  <h4 className="font-semibold text-xs text-slate-900 dark:text-white">
                    {hol.name}
                  </h4>
                  <p className="font-mono text-[11px] text-slate-400">{hol.date}</p>
                </div>
              </div>

              <Badge color={hol.is_optional ? 'yellow' : 'green'}>
                {hol.is_optional ? 'Optional' : 'Official Paid'}
              </Badge>
            </div>
          ))}
        </div>
      )}

      {/* Add Shift Modal */}
      <Modal
        isOpen={isShiftModalOpen}
        onClose={() => setIsShiftModalOpen(false)}
        title="Create New Shift"
        description="Specify shift start time, end time, and grace period."
      >
        <form onSubmit={handleAddShift} className="space-y-4 mt-2">
          <Input
            label="Shift Title"
            placeholder="e.g. European Client Shift"
            value={newShift.name}
            onChange={(e) => setNewShift({ ...newShift, name: e.target.value })}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start Time (HH:MM)"
              type="time"
              value={newShift.start_time}
              onChange={(e) => setNewShift({ ...newShift, start_time: e.target.value })}
              required
            />

            <Input
              label="End Time (HH:MM)"
              type="time"
              value={newShift.end_time}
              onChange={(e) => setNewShift({ ...newShift, end_time: e.target.value })}
              required
            />
          </div>

          <Input
            label="Grace Period (Minutes)"
            type="number"
            value={newShift.grace_period_minutes}
            onChange={(e) => setNewShift({ ...newShift, grace_period_minutes: Number(e.target.value) })}
          />

          <label className="flex items-center gap-2 cursor-pointer text-xs select-none">
            <input
              type="checkbox"
              checked={newShift.is_overnight}
              onChange={(e) => setNewShift({ ...newShift, is_overnight: e.target.checked })}
              className="rounded text-brand-600"
            />
            <span>This shift crosses midnight (Overnight shift)</span>
          </label>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsShiftModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Create Shift
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ShiftsPage;
