import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid
} from 'recharts';
import { statsApi } from '../api/client';
import { TrendingUp, PieChart as PieIcon, BarChart3 } from 'lucide-react';

const TYPE_COLORS = ['#ef4444', '#f97316', '#eab308', '#38bdf8', '#22c55e'];

export default function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => statsApi.get().then(r => r.data),
    refetchInterval: 15000,
  });

  const hourlyData = stats?.violations_by_hour?.map((h: { hour: number; count: number }) => ({
    hour: `${String(h.hour).padStart(2, '0')}:00`,
    violations: h.count,
  })) ?? [];

  const pieData = stats?.violations_by_type
    ? Object.entries(stats.violations_by_type).map(([name, value]) => ({ name, value }))
    : [];

  const camData = stats?.camera_stats?.map((c: { camera_id: string; total_violations: number }) => ({
    camera: c.camera_id,
    violations: c.total_violations,
  })) ?? [];

  if (isLoading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div className="spinner" />
    </div>
  );

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Analytics</div>
          <div className="page-subtitle">Violation trends and camera performance breakdown</div>
        </div>
      </div>
      <div className="page-body">
        <div className="grid-2" style={{ marginBottom: '1.25rem' }}>
          {/* Hourly bar chart */}
          <div className="card">
            <div className="section-header">
              <span className="section-title">Hourly Violations (Today)</span>
              <BarChart3 size={15} style={{ color: 'var(--text-muted)' }} />
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={hourlyData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="hour" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} axisLine={false} tickLine={false} interval={2} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="violations" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Pie chart by type */}
          <div className="card">
            <div className="section-header">
              <span className="section-title">By Violation Type</span>
              <PieIcon size={15} style={{ color: 'var(--text-muted)' }} />
            </div>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="45%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false} fontSize={10}>
                    {pieData.map((_: unknown, i: number) => <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No data yet
              </div>
            )}
          </div>
        </div>

        {/* Camera comparison */}
        {camData.length > 0 && (
          <div className="card">
            <div className="section-header">
              <span className="section-title">Violations by Camera</span>
              <TrendingUp size={15} style={{ color: 'var(--text-muted)' }} />
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={camData} layout="vertical" margin={{ top: 4, right: 20, left: 20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="camera" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} width={90} />
                <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="violations" fill="#f97316" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </>
  );
}
