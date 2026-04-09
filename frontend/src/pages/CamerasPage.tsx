import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Camera, Plus, Trash2, MonitorPlay, X } from 'lucide-react';
import { camerasApi, BASE_URL as BASE } from '../api/client';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function CamerasPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [newId, setNewId] = useState('');
  const [newSrc, setNewSrc] = useState('');

  const { data: cameras = [], isLoading } = useQuery({
    queryKey: ['cameras'],
    queryFn: () => camerasApi.list().then(r => r.data),
    refetchInterval: 5000,
  });

  const addMut = useMutation({
    mutationFn: () => camerasApi.add(newId.trim(), newSrc.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cameras'] });
      setShowAdd(false); setNewId(''); setNewSrc('');
      toast.success(`Camera ${newId} added`);
    },
    onError: () => toast.error('Failed to add camera'),
  });

  const removeMut = useMutation({
    mutationFn: (id: string) => camerasApi.remove(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cameras'] }); toast.success('Camera removed'); },
    onError: () => toast.error('Failed to remove camera'),
  });

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Camera Management</div>
          <div className="page-subtitle">Add, monitor, and remove video streams</div>
        </div>
        {user?.role === 'admin' && (
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
            <Plus size={15} /> Add Camera
          </button>
        )}
      </div>

      <div className="page-body">
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <div className="spinner" />
          </div>
        ) : cameras.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <Camera size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              No cameras configured yet.
            </p>
            {user?.role === 'admin' && (
              <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
                <Plus size={15} /> Add Your First Camera
              </button>
            )}
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
              Supports webcam index (e.g. <code>0</code>), RTSP URLs, HTTP streams
            </p>
          </div>
        ) : (
          <div className="grid-3" style={{ gap: '1rem' }}>
            {cameras.map((cam: {
              camera_id: string; source: string; running: boolean;
              frame_count: number; error?: string; uptime_s: number;
            }) => (
              <div key={cam.camera_id} className={`card ${cam.running ? 'card--success' : cam.error ? 'card--danger' : ''}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className={`status-dot ${cam.running ? 'status-dot-online' : cam.error ? 'status-dot-error' : 'status-dot-offline'}`} />
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{cam.camera_id}</span>
                  </div>
                  {cam.running ? (
                    <span className="badge badge-success">● Online</span>
                  ) : (
                    <span className="badge badge-muted">Offline</span>
                  )}
                </div>

                <div style={{ width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: 8, overflow: 'hidden', marginBottom: '0.75rem' }}>
                  {cam.running ? (
                    <img 
                      src={`${BASE}/api/cameras/${cam.camera_id}/stream`} 
                      alt="preview" 
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                    />
                  ) : (
                    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                      <Camera size={24} style={{ opacity: 0.2 }} />
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: '0.5rem' }}>
                  <MonitorPlay size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {cam.source}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', margin: '0.75rem 0' }}>
                  <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '0.5rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{cam.frame_count}</div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Frames</div>
                  </div>
                  <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '0.5rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{cam.uptime_s}s</div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Uptime</div>
                  </div>
                </div>

                {cam.error && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--accent-danger)', background: 'var(--accent-danger-dim)',
                    padding: '0.35rem 0.6rem', borderRadius: 6, marginBottom: '0.5rem' }}>⚠ {cam.error}</div>
                )}

                {user?.role === 'admin' && (
                  <button className="btn btn-danger btn-sm w-full" style={{ justifyContent: 'center', marginTop: '0.5rem' }}
                    onClick={() => removeMut.mutate(cam.camera_id)}>
                    <Trash2 size={12} /> Remove Camera
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add modal */}
      {showAdd && (
        <div className="modal-overlay" onClick={() => setShowAdd(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 420 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <span style={{ fontWeight: 700, fontSize: '1rem' }}>Add Camera</span>
              <button onClick={() => setShowAdd(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                <X size={18} />
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Camera ID</label>
                <input className="input" placeholder="e.g. cam-lobby, rtsp-entrance"
                  value={newId} onChange={e => setNewId(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Source</label>
                <input className="input" placeholder="0  or  rtsp://192.168.1.x/stream  or  http://..."
                  value={newSrc} onChange={e => setNewSrc(e.target.value)} />
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Use <code>0</code> for default webcam, RTSP URL for IP cameras, or HTTP URL for stream.
              </p>
              <button className="btn btn-primary w-full" style={{ justifyContent: 'center' }}
                onClick={() => addMut.mutate()}
                disabled={!newId.trim() || !newSrc.trim() || addMut.isPending}>
                {addMut.isPending ? 'Connecting…' : <><Plus size={14} /> Add Camera</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
