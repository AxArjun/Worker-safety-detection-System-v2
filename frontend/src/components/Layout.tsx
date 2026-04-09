import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, ShieldAlert, Camera, BarChart3,
  Bell, LogOut, Wifi, ScanFace
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/' },
  { label: 'Incidents', icon: ShieldAlert, to: '/incidents' },
  { label: 'Cameras', icon: Camera, to: '/cameras' },
  { label: 'Analytics', icon: BarChart3, to: '/analytics' },
  { label: 'Alerts', icon: Bell, to: '/alerts' },
  { label: 'PPE Analyzer', icon: ScanFace, to: '/ppe-analyzer' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const { isConnected } = useWebSocket();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <ShieldAlert size={18} />
          </div>
          <div>
            <div className="sidebar-logo-text">SafeGuard AI</div>
            <div className="sidebar-logo-sub">Safety Monitor</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-group-label">Navigation</div>
          {navItems.map(({ label, icon: Icon, to }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}

          <div className="nav-group-label" style={{ marginTop: '0.75rem' }}>System</div>
          <div style={{ padding: '0.5rem 1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0.5rem 0',
              borderBottom: '1px solid var(--border-subtle)' }}>
              <Wifi size={13} style={{ color: isConnected ? 'var(--accent-success)' : 'var(--accent-danger)' }} 
                className={isConnected ? 'status-live' : ''} />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                {isConnected ? 'Real-time Link Active' : 'Disconnected (Reconnect...)'}
              </span>
            </div>
          </div>
        </nav>

        {/* User footer */}
        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0.5rem 0.5rem', borderRadius: 'var(--radius-md)', cursor: 'default' }}>
            <div style={{ width: 30, height: 30, borderRadius: '50%', background: 'linear-gradient(135deg, #f97316, #ea580c)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: '#fff', flexShrink: 0 }}>
              {user?.email?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.email}
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                {user?.role}
              </div>
            </div>
            <button onClick={handleLogout} title="Logout"
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4, borderRadius: 6,
                transition: 'color 0.2s', display: 'flex', alignItems: 'center' }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--accent-danger)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}>
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
