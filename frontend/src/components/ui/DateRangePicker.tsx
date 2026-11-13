import React, { useState } from 'react';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';
import { Calendar as CalendarIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface DateRange {
  startDate: string; // YYYY-MM-DD
  endDate: string;   // YYYY-MM-DD
}

export interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  className?: string;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  value,
  onChange,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const presets = [
    {
      label: 'Today',
      getRange: () => {
        const today = format(new Date(), 'yyyy-MM-dd');
        return { startDate: today, endDate: today };
      },
    },
    {
      label: 'Yesterday',
      getRange: () => {
        const yest = format(subDays(new Date(), 1), 'yyyy-MM-dd');
        return { startDate: yest, endDate: yest };
      },
    },
    {
      label: 'Last 7 Days',
      getRange: () => {
        const end = format(new Date(), 'yyyy-MM-dd');
        const start = format(subDays(new Date(), 6), 'yyyy-MM-dd');
        return { startDate: start, endDate: end };
      },
    },
    {
      label: 'Last 30 Days',
      getRange: () => {
        const end = format(new Date(), 'yyyy-MM-dd');
        const start = format(subDays(new Date(), 29), 'yyyy-MM-dd');
        return { startDate: start, endDate: end };
      },
    },
    {
      label: 'This Month',
      getRange: () => {
        const start = format(startOfMonth(new Date()), 'yyyy-MM-dd');
        const end = format(endOfMonth(new Date()), 'yyyy-MM-dd');
        return { startDate: start, endDate: end };
      },
    },
  ];

  return (
    <div className={cn('relative inline-block', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <CalendarIcon className="h-4 w-4 text-brand-600 dark:text-brand-400" />
        <span>
          {value.startDate === value.endDate
            ? value.startDate
            : `${value.startDate} — ${value.endDate}`}
        </span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-20"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 z-30 mt-2 w-72 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Quick Presets
            </div>
            <div className="grid grid-cols-2 gap-1.5 mb-4">
              {presets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => {
                    onChange(preset.getRange());
                    setIsOpen(false);
                  }}
                  className="rounded-lg px-2.5 py-1.5 text-left text-xs font-medium text-slate-700 hover:bg-brand-50 hover:text-brand-600 dark:text-slate-300 dark:hover:bg-brand-950/40 dark:hover:text-brand-400 transition-colors"
                >
                  {preset.label}
                </button>
              ))}
            </div>

            <div className="border-t border-slate-100 dark:border-slate-800 pt-3">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Custom Dates
              </div>
              <div className="space-y-2">
                <div>
                  <label className="text-[11px] text-slate-500 dark:text-slate-400">Start Date</label>
                  <input
                    type="date"
                    value={value.startDate}
                    onChange={(e) => onChange({ ...value, startDate: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-500 dark:text-slate-400">End Date</label>
                  <input
                    type="date"
                    value={value.endDate}
                    onChange={(e) => onChange({ ...value, endDate: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
                  />
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default DateRangePicker;
