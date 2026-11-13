import React, { useState } from 'react';
import { FileSpreadsheet, Download, FileText, Calendar, Filter, CheckCircle2 } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Select from '../../components/ui/Select';
import Input from '../../components/ui/Input';
import toast from 'react-hot-toast';

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState('monthly');
  const [department, setDepartment] = useState('all');
  const [exportFormat, setExportFormat] = useState('xlsx');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleExport = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      toast.success(`Generated ${reportType.toUpperCase()} attendance report (${exportFormat.toUpperCase()})`);
    }, 1200);
  };

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Attendance Reports & Payroll Exports
        </h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Generate payroll-ready attendance registers, overtime summaries, and department audit packages.
        </p>
      </div>

      <Card>
        <Card.Header>
          <Card.Title>Configure Export Parameters</Card.Title>
          <Card.Description>Select the time period, department scope, and output format</Card.Description>
        </Card.Header>
        <Card.Content className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Report Frequency"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              options={[
                { value: 'daily', label: 'Daily Attendance Register' },
                { value: 'monthly', label: 'Monthly Summary (Payroll Sheet)' },
                { value: 'overtime', label: 'Overtime & Late Arrival Audit' },
                { value: 'custom', label: 'Custom Date Range Export' },
              ]}
            />

            <Select
              label="Department Filter"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              options={[
                { value: 'all', label: 'All Departments' },
                { value: 'eng', label: 'Engineering' },
                { value: 'design', label: 'Product & Design' },
                { value: 'ops', label: 'Operations' },
                { value: 'sales', label: 'Sales & Marketing' },
              ]}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Report Month / Period"
              type="month"
              defaultValue="2026-11"
            />

            <Select
              label="Export Format"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              options={[
                { value: 'xlsx', label: 'Microsoft Excel (.xlsx)' },
                { value: 'csv', label: 'Standard CSV (.csv)' },
                { value: 'pdf', label: 'Printable Document (.pdf)' },
              ]}
            />
          </div>

          {/* Options */}
          <div className="rounded-xl border border-slate-200/80 bg-slate-50 p-4 text-xs dark:border-slate-800 dark:bg-slate-850 space-y-2">
            <p className="font-semibold text-slate-700 dark:text-slate-300">
              Additional Parameters
            </p>
            <div className="space-y-2 text-slate-600 dark:text-slate-400">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded text-brand-600" />
                <span>Include late penalties and grace period minutes calculation</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded text-brand-600" />
                <span>Include employee unique ID and designated shift names</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="rounded text-brand-600" />
                <span>Attach AI facial recognition confidence scores</span>
              </label>
            </div>
          </div>

          <div className="pt-3 flex justify-end">
            <Button
              variant="primary"
              size="lg"
              isLoading={isGenerating}
              onClick={handleExport}
              leftIcon={<Download className="h-4 w-4" />}
            >
              Generate & Download Report
            </Button>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default ReportsPage;
