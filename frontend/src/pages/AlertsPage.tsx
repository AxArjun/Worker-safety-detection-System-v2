import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle, Camera } from 'lucide-react';
import { alertsApi } from '../api/client';

export default function AlertsPage() {
  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => alertsApi.recent().then(r => r.data),
    refetchInterval: 5000,
  });

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Alert Feed</div>
          <div className="page-subtitle">Real-time safety alert notifications</div>
        </div>
        <span className="badge badge-danger" style={{ fontSize: '0.8rem', padding: '4px 10px' }}>
          {alerts.length} recent
        </span>
      </div>
      <div className="page-body">
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}><div className="spinner" /></div>
        ) : alerts.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <CheckCircle size={48} style={{ color: 'var(--accent-success)', marginBottom: '1rem' }} />
            <p style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>No recent alerts</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.83rem', marginTop: '0.5rem' }}>
              Alerts appear here when violations are detected
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {alerts.map((a: { timestamp: number; camera_id: string; violation_type: string; snapshot_path?: string }, i: number) => (
              <div key={i} className="card" style={{ display: 'flex', gap: '1rem', alignItems: 'center', padding: '0.9rem 1.25rem',
                borderLeft: '3px solid var(--accent-danger)' }}>
                <div style={{ width: 36, height: 36, background: 'var(--accent-danger-dim)', borderRadius: 10,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <AlertTriangle size={18} style={{ color: 'var(--accent-danger)' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{a.violation_type}</span>
                    <span className="badge badge-danger">Critical</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <Camera size={12} />
                    <span>{a.camera_id}</span>
                    {a.snapshot_path && <span>· Snapshot saved</span>}
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {new Date(a.timestamp * 1000).toLocaleTimeString()}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {new Date(a.timestamp * 1000).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
