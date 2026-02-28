'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const WardMap = dynamic(() => import('@/app/components/WardMap'), { ssr: false });
import {
  BarChart3,
  TrendingUp,
  Users,
  MapPin,
  AlertTriangle,
  CheckCircle,
  Clock,
  Brain,
  Activity,
  Loader2,
  RefreshCw,
  Trophy,
  FileText,
  Shield,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import {
  fetchDashboard,
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  STATUS_COLORS,
  type FullDashboard,
  type DashboardStats,
  type CategoryBreakdown,
  type WardHeatmap,
  type TrendData,
  type WorkerLeaderboard,
  type RecentReport,
} from '@/lib/api';

export default function AdminDashboard() {
  const [dashboard, setDashboard] = useState<FullDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchDashboard();
      setDashboard(data);
    } catch {
      // Use fallback data
      setDashboard(getFallbackDashboard());
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin text-emerald-600 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboard) return null;

  const { stats, categories, heatmap, trends, leaderboard, recent_reports } = dashboard;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-gray-500 text-sm mt-0.5">
                Municipal sanitation operations overview
              </p>
            </div>
            <button
              onClick={loadDashboard}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 transition text-sm font-medium"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* ==================== STAT CARDS ==================== */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard
            icon={FileText}
            label="Total Reports"
            value={stats.total_reports.toLocaleString()}
            sub={`+${stats.reports_today} today`}
            color="blue"
          />
          <StatCard
            icon={Clock}
            label="Pending Tasks"
            value={stats.pending_tasks.toString()}
            sub={`${stats.in_progress_tasks} in progress`}
            color="amber"
          />
          <StatCard
            icon={CheckCircle}
            label="Completed Today"
            value={stats.completed_today.toString()}
            sub={`Avg ${stats.avg_resolution_hours}h`}
            color="emerald"
          />
          <StatCard
            icon={Brain}
            label="AI Accuracy"
            value={`${stats.ai_accuracy}%`}
            sub="Classification"
            color="purple"
          />
          <StatCard
            icon={Users}
            label="Active Workers"
            value={stats.active_workers.toString()}
            sub={`${stats.wards_covered} wards`}
            color="teal"
          />
        </div>

        {/* ==================== CHARTS ROW ==================== */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Category Pie Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-emerald-600" />
              Reports by Category
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categories}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="count"
                    nameKey="category"
                    label={(props) => {
                      const p = props as unknown as Record<string, unknown>;
                      const cat = String(p.category || '');
                      const pct = p.percentage;
                      return `${(CATEGORY_LABELS[cat] || cat).split(' ')[0]} ${pct}%`;
                    }}
                    labelLine={false}
                  >
                    {categories.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CATEGORY_COLORS[entry.category] || '#94a3b8'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: unknown, name: unknown) => [
                      String(value),
                      CATEGORY_LABELS[String(name)] || String(name),
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Legend */}
            <div className="grid grid-cols-2 gap-2 mt-2">
              {categories.slice(0, 6).map((cat) => (
                <div key={cat.category} className="flex items-center gap-2 text-xs">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{
                      backgroundColor: CATEGORY_COLORS[cat.category] || '#94a3b8',
                    }}
                  />
                  <span className="text-gray-600 truncate">
                    {CATEGORY_LABELS[cat.category] || cat.category}
                  </span>
                  <span className="text-gray-400 ml-auto">{cat.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Trends Line Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-600" />
              7-Day Trend
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(v) => v.slice(5)}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="reports_filed"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="Reports Filed"
                  />
                  <Line
                    type="monotone"
                    dataKey="tasks_completed"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="Tasks Completed"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* ==================== MAP + WARD SUMMARY ==================== */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <MapPin className="h-5 w-5 text-emerald-600" />
            Ward-Level Heatmap
            <span className="ml-auto text-xs font-normal text-gray-400">Click a ward for details</span>
          </h3>
          <WardMap wards={heatmap} height="420px" />

          {/* Compact ward summary below map */}
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            {heatmap
              .sort((a, b) => b.open_reports - a.open_reports)
              .slice(0, 10)
              .map((ward) => (
                <div
                  key={ward.ward_number}
                  className={`rounded-lg p-2.5 text-xs border ${
                    ward.risk_level === 'high'
                      ? 'border-red-200 bg-red-50'
                      : ward.risk_level === 'medium'
                      ? 'border-amber-200 bg-amber-50'
                      : 'border-green-200 bg-green-50'
                  }`}
                >
                  <div className="font-semibold text-gray-900 truncate">{ward.name}</div>
                  <div className="text-gray-500 mt-0.5">{ward.open_reports} open · {ward.severity_avg} avg</div>
                  <span
                    className={`inline-block mt-1 text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                      ward.risk_level === 'high'
                        ? 'bg-red-100 text-red-700'
                        : ward.risk_level === 'medium'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-green-100 text-green-700'
                    }`}
                  >
                    {ward.risk_level.toUpperCase()}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* ==================== LEADERBOARD & TABLE ==================== */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Ward table (compact) */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-emerald-600" />
              Ward Data Table
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-gray-100">
                    <th className="pb-2 font-medium">Ward</th>
                    <th className="pb-2 font-medium">Open Reports</th>
                    <th className="pb-2 font-medium">Avg Severity</th>
                    <th className="pb-2 font-medium">Risk Level</th>
                  </tr>
                </thead>
                <tbody>
                  {heatmap
                    .sort((a, b) => b.open_reports - a.open_reports)
                    .map((ward) => (
                      <tr key={ward.ward_number} className="border-b border-gray-50">
                        <td className="py-2.5 font-medium">{ward.name}</td>
                        <td className="py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 max-w-24 bg-gray-100 rounded-full h-2">
                              <div
                                className="h-2 rounded-full bg-emerald-500"
                                style={{
                                  width: `${Math.min(100, (ward.open_reports / 40) * 100)}%`,
                                }}
                              />
                            </div>
                            <span>{ward.open_reports}</span>
                          </div>
                        </td>
                        <td className="py-2.5">{ward.severity_avg}</td>
                        <td className="py-2.5">
                          <span
                            className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                              ward.risk_level === 'high'
                                ? 'bg-red-100 text-red-700'
                                : ward.risk_level === 'medium'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-green-100 text-green-700'
                            }`}
                          >
                            {ward.risk_level.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Worker Leaderboard */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-500" />
              Top Workers
            </h3>
            <div className="space-y-3">
              {leaderboard.map((worker, i) => (
                <div
                  key={worker.worker_id}
                  className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      i === 0
                        ? 'bg-amber-100 text-amber-700'
                        : i === 1
                        ? 'bg-gray-200 text-gray-700'
                        : i === 2
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-gray-900 truncate">
                      {worker.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {worker.completed_this_week} tasks · {worker.avg_rating}★
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-400">
                      ~{worker.avg_resolution_hours}h avg
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ==================== RECENT REPORTS ==================== */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-600" />
            Recent Reports
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100">
                  <th className="pb-2 font-medium">Report ID</th>
                  <th className="pb-2 font-medium">Category</th>
                  <th className="pb-2 font-medium">Severity</th>
                  <th className="pb-2 font-medium">Ward</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Description</th>
                </tr>
              </thead>
              <tbody>
                {recent_reports.map((report) => (
                  <tr key={report.report_id} className="border-b border-gray-50">
                    <td className="py-2.5 font-mono text-xs">{report.report_id}</td>
                    <td className="py-2.5">
                      {CATEGORY_LABELS[report.category] || report.category}
                    </td>
                    <td className="py-2.5">
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                          report.severity_score >= 8
                            ? 'bg-red-100 text-red-700'
                            : report.severity_score >= 5
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {report.severity_score}/10
                      </span>
                    </td>
                    <td className="py-2.5">Ward {report.ward_number}</td>
                    <td className="py-2.5">
                      <span
                        className="text-xs font-medium px-2 py-0.5 rounded"
                        style={{
                          backgroundColor: (STATUS_COLORS[report.status] || '#6b7280') + '20',
                          color: STATUS_COLORS[report.status] || '#6b7280',
                        }}
                      >
                        {report.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-2.5 text-gray-600 truncate max-w-60">
                      {report.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer info */}
        <div className="text-center text-xs text-gray-400 py-4">
          <Shield className="h-4 w-4 inline mr-1" />
          Powered by Amazon Bedrock · Data refreshed at{' '}
          {dashboard.generated_at
            ? new Date(dashboard.generated_at).toLocaleString()
            : 'now'}
        </div>
      </div>
    </div>
  );
}

// Stat Card component
function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  sub: string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    purple: 'bg-purple-50 text-purple-600',
    teal: 'bg-teal-50 text-teal-600',
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
          <Icon className="h-4 w-4" />
        </div>
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-400 mt-0.5">{sub}</div>
    </div>
  );
}

// Fallback dashboard data (matches Lambda mock data)
function getFallbackDashboard(): FullDashboard {
  return {
    stats: {
      total_reports: 1247,
      reports_today: 34,
      pending_tasks: 89,
      in_progress_tasks: 45,
      completed_today: 23,
      avg_resolution_hours: 6.4,
      citizen_satisfaction: 4.2,
      ai_accuracy: 94.6,
      active_workers: 67,
      wards_covered: 24,
    },
    categories: [
      { category: 'garbage_pile', count: 423, percentage: 33.9 },
      { category: 'overflowing_drain', count: 312, percentage: 25.0 },
      { category: 'blocked_sewer', count: 198, percentage: 15.9 },
      { category: 'stagnant_water', count: 156, percentage: 12.5 },
      { category: 'medical_waste', count: 67, percentage: 5.4 },
      { category: 'animal_carcass', count: 34, percentage: 2.7 },
      { category: 'other', count: 57, percentage: 4.6 },
    ],
    heatmap: Array.from({ length: 24 }, (_, i) => ({
      ward_number: i + 1,
      name: `Ward ${i + 1}`,
      center_lat: 19.0 + (i + 1) * 0.005,
      center_lng: 72.8 + (i + 1) * 0.003,
      open_reports: Math.max(0, 30 - (i + 1) + ((i + 1) % 7) * 3),
      severity_avg: Math.round((3 + ((i + 1) % 5) * 1.2) * 10) / 10,
      risk_level: ([3, 7, 15, 22].includes(i + 1)
        ? 'high'
        : (i + 1) % 3 === 0
        ? 'medium'
        : 'low') as 'high' | 'medium' | 'low',
    })),
    trends: Array.from({ length: 7 }, (_, d) => {
      const date = new Date(2026, 1, 22 + d);
      return {
        date: date.toISOString().slice(0, 10),
        reports_filed: 30 + d * 3 + (d % 3) * 5,
        tasks_completed: 25 + d * 2 + (d % 4) * 3,
        avg_severity: Math.round((4.5 + (d % 3) * 0.5) * 10) / 10,
      };
    }),
    leaderboard: Array.from({ length: 5 }, (_, i) => ({
      worker_id: `W-${String(i + 1).padStart(3, '0')}`,
      name: `Worker ${i + 1}`,
      completed_this_week: Math.max(1, 20 - (i + 1) * 2 + ((i + 1) % 3)),
      avg_rating: Math.round((4.0 + ((i + 1) % 5) * 0.15) * 10) / 10,
      avg_resolution_hours: Math.round((3.0 + (i + 1) * 0.5) * 10) / 10,
    })).sort((a, b) => b.completed_this_week - a.completed_this_week),
    recent_reports: [
      {
        report_id: 'RPT-260228-XYZ',
        category: 'garbage_pile',
        severity_score: 7,
        ward_number: 15,
        status: 'in_progress',
        created_at: '2026-02-28T09:30:00Z',
        description: 'Large garbage accumulation near apartment complex',
      },
      {
        report_id: 'RPT-260228-ABC',
        category: 'stagnant_water',
        severity_score: 8,
        ward_number: 3,
        status: 'pending',
        created_at: '2026-02-28T08:15:00Z',
        description: 'Stagnant water pooling near playground',
      },
      {
        report_id: 'RPT-260227-DEF',
        category: 'blocked_sewer',
        severity_score: 6,
        ward_number: 22,
        status: 'completed',
        created_at: '2026-02-27T16:45:00Z',
        description: 'Sewer blockage causing street flooding',
      },
    ],
    generated_at: new Date().toISOString(),
  };
}
