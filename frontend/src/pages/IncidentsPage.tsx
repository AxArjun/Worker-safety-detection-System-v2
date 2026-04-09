import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShieldAlert, Trash2, Search, Filter, Image, X } from 'lucide-react';
import { violationsApi } from '../api/client';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const TYPE_COLORS: Record<string, string> = {
  NO_HELMET: 'badge-danger',
  NO_VEST: 'badge-warning',
  UNSAFE_ZONE: 'badge-info',
  NO_PPE: 'badge-muted',
};

export default function IncidentsPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [preview, setPreview] = useState<{ id: number; path: string } | null>(null);

  const { data: violations = [], isLoading } = useQuery({
    queryKey: ['violations', typeFilter],
    queryFn: () => violationsApi.list({ type: typeFilter || undefined, limit: 100 }).then(r => r.data),
    refetchInterval: 10000,
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => violationsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['violations'] }); toast.success('Deleted'); },
    onError: () => toast.error('Delete failed'),
  });

  const filtered = violations.filter((v: { camera_id: string; violation_type: string }) =>
    v.camera_id.toLowerCase().includes(search.toLowerCase()) ||
    v.violation_type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Incident Log</div>
          <div className="page-subtitle">All safety violations with filtering and history</div>
        </div>
        <span className="section-count">{violations.length} records</span>
      </div>

      <div className="page-body">
        {/* Filters */}
        <div className="card" style={{ marginBottom: '1rem', padding: '0.85rem 1.25rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input className="input" style={{ paddingLeft: '2rem' }} placeholder="Search camera ID or type…"
                value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div style={{ position: 'relative' }}>
              <Filter size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
              <select className="input" style={{ paddingLeft: '2rem', width: 180, cursor: 'pointer', appearance: 'none' }}
                value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
                <option value="">All Types</option>
                <option value="NO_HELMET">No Helmet</option>
                <option value="NO_VEST">No Vest</option>
                <option value="UNSAFE_ZONE">Unsafe Zone</option>
                <option value="NO_PPE">No PPE</option>
              </select>
            </div>
            {(search || typeFilter) && (
              <button className="btn btn-outline btn-sm" onClick={() => { setSearch(''); setTypeFilter(''); }}>
                <X size={13} /> Clear
              </button>
            )}
          </div>
        </div>

        {/* Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {isLoading ? (
            <div style={{ padding: '3rem', display: 'flex', justifyContent: 'center' }}>
              <div className="spinner" />
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <ShieldAlert size={36} style={{ marginBottom: '0.75rem', opacity: 0.3 }} />
              <p>No incidents found</p>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '1.25rem' }}>ID</th>
                  <th>Snapshot</th>
                  <th>Type</th>
                  <th>Camera</th>
                  <th>Source</th>
                  <th>Confidence</th>
                  <th>Timestamp</th>
                  {user?.role === 'admin' && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {filtered.map((v: {
                  id: number; violation_type: string; camera_id: string;
                  camera_source?: string; confidence?: number; timestamp: string;
                  image_path?: string;
                }) => (
                  <tr key={v.id}>
                    <td style={{ paddingLeft: '1.25rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                      #{v.id}
                    </td>
                    <td>
                      {v.image_path ? (
                        <button onClick={() => setPreview({ id: v.id, path: v.image_path! })}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                          <img src={`${BASE}/snapshots/${v.image_path.split('/').pop()}`}
                            alt="snapshot" style={{ width: 48, height: 36, objectFit: 'cover', borderRadius: 5, display: 'block' }} />
                        </button>
                      ) : (
                        <div style={{ width: 48, height: 36, background: 'var(--bg-elevated)', borderRadius: 5,
                          display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Image size={14} style={{ color: 'var(--text-muted)' }} />
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${TYPE_COLORS[v.violation_type] ?? 'badge-muted'}`}>
                        {v.violation_type}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.83rem' }}>{v.camera_id}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem', maxWidth: 120 }} className="truncate">
                      {v.camera_source ?? '–'}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.83rem' }}>
                      {v.confidence ? `${(v.confidence * 100).toFixed(1)}%` : '–'}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {new Date(v.timestamp).toLocaleString()}
                    </td>
                    {user?.role === 'admin' && (
                      <td>
                        <button className="btn btn-danger btn-sm"
                          onClick={() => deleteMut.mutate(v.id)}
                          disabled={deleteMut.isPending}>
                          <Trash2 size={12} />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Image preview modal */}
      {preview && (
        <div className="modal-overlay" onClick={() => setPreview(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 700, width: '90vw' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span style={{ fontWeight: 600 }}>Violation #{preview.id} Snapshot</span>
              <button onClick={() => setPreview(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                <X size={18} />
              </button>
            </div>
            <img src={`${BASE}/snapshots/${preview.path.split('/').pop()}`}
              alt="violation snapshot" style={{ width: '100%', borderRadius: 'var(--radius-md)', display: 'block' }} />
          </div>
        </div>
      )}
    </>
  );
}
