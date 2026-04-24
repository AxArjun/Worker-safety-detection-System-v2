import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import {
  ShieldAlert, Camera, TrendingUp, Clock, AlertTriangle, Activity
} from 'lucide-react';
import { statsApi, violationsApi, alertsApi, camerasApi, BASE_URL as BASE } from '../api/client';

function StatCard({ label, value, icon: Icon, color, sub }: {
  label: string; value: string | number; icon: React.ElementType;
  color: string; sub?: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-card-icon" style={{ background: `${color}20` }}>
        <Icon size={18} style={{ color }} />
      </div>
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value" style={{ color }}>{value}</div>
      {sub && <div className="stat-card-sub">{sub}</div>}
    </div>
  );
}

function AlertBannerItem({ alert }: { alert: { camera_id: string; violation_type: string; timestamp: number } }) {
  return (
    <div className="alert-banner">
      <div className="alert-dot" />
      <AlertTriangle size={15} style={{ color: 'var(--accent-danger)', flexShrink: 0 }} />
      <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', flex: 1 }}>
        <strong>{alert.violation_type}</strong> detected on <strong>{alert.camera_id}</strong>
      </span>
      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        {new Date(alert.timestamp * 1000).toLocaleTimeString()}
      </span>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats } = useQuery({ queryKey: ['stats'], queryFn: () => statsApi.get().then(r => r.data), refetchInterval: 5000 });
  const { data: violations } = useQuery({ queryKey: ['violations-recent'], queryFn: () => violationsApi.list({ limit: 5 }).then(r => r.data), refetchInterval: 5000 });
  const { data: alerts } = useQuery({ queryKey: ['alerts'], queryFn: () => alertsApi.recent().then(r => r.data), refetchInterval: 5000 });
  const { data: cameras } = useQuery({ queryKey: ['cameras'], queryFn: () => camerasApi.list().then(r => r.data), refetchInterval: 10000 });

  const activeCam = cameras?.find((c: any) => c.running);

  const hourlyData = stats?.violations_by_hour?.map((h: { hour: number; count: number }) => ({
    time: `${String(h.hour).padStart(2, '0')}:00`,
    violations: h.count,
  })) ?? [];

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Operations Dashboard</div>
          <div className="page-subtitle">Real-time safety monitoring overview</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="status-dot status-dot-online" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Live</span>
        </div>
      </div>

      <div className="page-body">
        {/* Recent alerts */}
        {alerts && alerts.length > 0 && (
          <AlertBannerItem alert={alerts[0]} />
        )}

        {/* Stats cards */}
        <div className="stats-grid">
          <StatCard label="Total Violations" value={stats?.total_violations ?? '–'} icon={ShieldAlert} color="var(--accent-danger)" sub="All time" />
          <StatCard label="Today" value={stats?.today_violations ?? '–'} icon={Clock} color="var(--accent-warning)" sub="Last 24h" />
          <StatCard label="Active Cameras" value={stats?.cameras_active ?? '–'} icon={Camera} color="var(--accent-success)" sub="Streams online" />
          <StatCard label="NO_HELMET" value={stats?.violations_by_type?.NO_HELMET ?? 0} icon={Activity} color="var(--accent-primary)" sub="Most common" />
        </div>

        <div className="grid-2" style={{ gap: '1.25rem' }}>
          {/* Left: Chart */}
          <div className="card">
            <div className="section-header">
              <span className="section-title">Violations (Today by Hour)</span>
              <TrendingUp size={15} style={{ color: 'var(--text-muted)' }} />
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={hourlyData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="vGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="time" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="violations" stroke="#ef4444" strokeWidth={2} fill="url(#vGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Right: Recent violations */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="section-header">
              <span className="section-title">Recent Incidents</span>
              <span className="section-count">{violations?.length ?? 0}</span>
            </div>
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {violations && violations.length > 0 ? violations.map((v: {
                id: number; violation_type: string; camera_id: string;
                timestamp: string; confidence: number; image_path?: string;
              }) => (
                <div key={v.id} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '0.65rem 0',
                  borderBottom: '1px solid var(--border-subtle)'
                }}>
                  {v.image_path ? (
                    <img src={`${BASE}/snapshots/${v.image_path.split('/').pop()}`}
                      alt="snapshot" style={{ width: 42, height: 32, objectFit: 'cover', borderRadius: 6, flexShrink: 0 }} />
                  ) : (
                    <div style={{
                      width: 42, height: 32, background: 'var(--bg-elevated)', borderRadius: 6, flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <ShieldAlert size={14} style={{ color: 'var(--accent-danger)' }} />
                    </div>
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{v.violation_type}</div>
                    <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>{v.camera_id}</div>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'right', flexShrink: 0 }}>
                    <div>{new Date(v.timestamp).toLocaleDateString()}</div>
                    <div>{new Date(v.timestamp).toLocaleTimeString()}</div>
                  </div>
                </div>
              )) : (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  No violations yet
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Live Feed placeholder */}
        <div className="card" style={{ marginTop: '1.25rem' }}>
          <div className="section-header" style={{ marginBottom: '0.75rem' }}>
            <span className="section-title">Live Camera Feed</span>
            <span className="badge badge-danger">● LIVE</span>
          </div>
          <div className="feed-container" style={{ minHeight: 400, background: '#000', borderRadius: 12, overflow: 'hidden', position: 'relative' }}>
            {activeCam ? (
              <img
                src={`${BASE}/api/cameras/${activeCam.camera_id}/stream`}
                alt="Live stream"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : (
              <div className="feed-placeholder" style={{ height: 400 }}>
                <Camera size={48} style={{ opacity: 0.3 }} />
                <p style={{ fontSize: '0.85rem' }}>No active cameras found</p>
                <p style={{ fontSize: '0.75rem' }}>Add a camera in the Management page to see live feed</p>
              </div>
            )}
            {activeCam && (
              <div style={{ position: 'absolute', top: 12, right: 12, display: 'flex', gap: 8 }}>
                <div className="badge badge-danger">● LIVE</div>
                <div style={{ background: 'rgba(0,0,0,0.6)', padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', color: '#fff' }}>
                  {activeCam.camera_id}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
