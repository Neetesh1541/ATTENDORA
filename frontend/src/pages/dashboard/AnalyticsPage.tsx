import React, { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Camera,
  Users,
  Calendar,
  Layers,
  ArrowUpRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import Card from '../../components/ui/Card';
import StatsCard from '../../components/ui/StatsCard';
import DateRangePicker from '../../components/ui/DateRangePicker';
import Badge from '../../components/ui/Badge';

export const AnalyticsPage: React.FC = () => {
  const [dateRange, setDateRange] = useState({
    startDate: '2026-11-01',
    endDate: '2026-11-13',
  });

  const trendData = [
    { date: 'Nov 01', attendance: 92, late: 4 },
    { date: 'Nov 03', attendance: 88, late: 8 },
    { date: 'Nov 05', attendance: 94, late: 3 },
    { date: 'Nov 07', attendance: 91, late: 5 },
    { date: 'Nov 09', attendance: 95, late: 2 },
    { date: 'Nov 11', attendance: 93, late: 6 },
    { date: 'Nov 13', attendance: 90, late: 7 },
  ];

  const shiftData = [
    { name: 'Morning Core (09:00)', onTime: 92, late: 6, absent: 2 },
    { name: 'Afternoon Shift (13:00)', onTime: 88, late: 8, absent: 4 },
    { name: 'Night Operations (21:00)', onTime: 96, late: 2, absent: 2 },
  ];

  const pieData = [
    { name: 'On-Time', value: 78, color: '#10b981' },
    { name: 'Late', value: 12, color: '#f59e0b' },
    { name: 'Absent / Leave', value: 10, color: '#f43f5e' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Organizational Analytics & Heatmaps
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Gain deep operational insights on punctuality, shift distributions, and camera metrics.
          </p>
        </div>

        <DateRangePicker value={dateRange} onChange={setDateRange} />
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          label="Avg Turnout Rate"
          value="92.4%"
          trend={{ value: 3.1, direction: 'up', label: 'vs previous period' }}
        />
        <StatsCard
          label="Avg Arrival Time"
          value="08:51 AM"
          trend={{ value: 4, direction: 'up', label: 'min earlier' }}
        />
        <StatsCard
          label="Late Arrival Index"
          value="5.8%"
          trend={{ value: 1.4, direction: 'down', label: 'improved' }}
        />
        <StatsCard
          label="Total Overtime Logged"
          value="184 hrs"
          trend={{ value: 0.5, direction: 'neutral', label: 'stable' }}
        />
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Attendance Percentage Trend */}
        <Card className="lg:col-span-8">
          <Card.Header>
            <Card.Title>Punctuality & Attendance Curve</Card.Title>
            <Card.Description>Daily turnout comparison with late arrivals overlay</Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(148, 163, 184, 0.2)" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} domain={[70, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '12px',
                      border: '1px solid #1e293b',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Line type="monotone" dataKey="attendance" stroke="#4f46e5" strokeWidth={3} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="late" stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card.Content>
        </Card>

        {/* Status Distribution Pie */}
        <Card className="lg:col-span-4">
          <Card.Header>
            <Card.Title>Status Distribution</Card.Title>
            <Card.Description>Overall attendance composition</Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="h-56 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-4 space-y-2 border-t border-slate-100 dark:border-slate-800 pt-3 text-xs">
              {pieData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-600 dark:text-slate-300">{item.name}</span>
                  </div>
                  <span className="font-semibold text-slate-900 dark:text-white">{item.value}%</span>
                </div>
              ))}
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Shift Comparison */}
      <Card>
        <Card.Header>
          <Card.Title>Shift Reliability Comparison</Card.Title>
          <Card.Description>On-time performance breakdown across assigned work shifts</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={shiftData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(148, 163, 184, 0.2)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderRadius: '12px',
                    border: '1px solid #1e293b',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="onTime" fill="#4f46e5" radius={[6, 6, 0, 0]} name="On-Time %" />
                <Bar dataKey="late" fill="#f59e0b" radius={[6, 6, 0, 0]} name="Late %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default AnalyticsPage;
