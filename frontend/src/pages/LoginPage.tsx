import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';
import toast from 'react-hot-toast';
import { ShieldAlert, Eye, EyeOff, Mail, Lock, Hash } from 'lucide-react';

type Mode = 'password' | 'otp-send' | 'otp-verify';

export default function LoginPage() {
  const { login, loginWithOtp } = useAuth();
  const [mode, setMode] = useState<Mode>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast.error(error?.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.sendOtp(email);
      setMode('otp-verify');
      toast.success('OTP sent! Check the backend console (dev mode).');
    } catch {
      toast.error('Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await loginWithOtp(email, otp);
      toast.success('Verified!');
    } catch {
      toast.error('Invalid or expired OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">
            <ShieldAlert size={22} />
          </div>
          <div>
            <div className="login-title">SafeGuard AI</div>
            <div className="login-sub">Worker Safety Platform</div>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="chip-tabs" style={{ marginBottom: '1.5rem' }}>
          <button className={`chip-tab ${mode === 'password' ? 'active' : ''}`}
            onClick={() => setMode('password')}>Password</button>
          <button className={`chip-tab ${mode !== 'password' ? 'active' : ''}`}
            onClick={() => setMode('otp-send')}>OTP Login</button>
        </div>

        {/* Password form */}
        {mode === 'password' && (
          <form onSubmit={handlePasswordLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="input-group">
              <label className="input-label">Email</label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input className="input" style={{ paddingLeft: '2rem' }} type="email" placeholder="admin@safeguard.local"
                  value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
            </div>
            <div className="input-group">
              <label className="input-label">Password</label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input className="input" style={{ paddingLeft: '2rem', paddingRight: '2.5rem' }}
                  type={showPw ? 'text' : 'password'} placeholder="••••••••"
                  value={password} onChange={e => setPassword(e.target.value)} required />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn btn-primary w-full" disabled={loading}
              style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        )}

        {/* OTP send form */}
        {mode === 'otp-send' && (
          <form onSubmit={handleSendOtp} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="input-group">
              <label className="input-label">Email</label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input className="input" style={{ paddingLeft: '2rem' }} type="email" placeholder="your@email.com"
                  value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
            </div>
            <button type="submit" className="btn btn-primary w-full" disabled={loading}
              style={{ justifyContent: 'center' }}>
              {loading ? 'Sending…' : 'Send OTP'}
            </button>
          </form>
        )}

        {/* OTP verify form */}
        {mode === 'otp-verify' && (
          <form onSubmit={handleVerifyOtp} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)' }}>
              OTP sent to <strong>{email}</strong>
            </p>
            <div className="input-group">
              <label className="input-label">6-digit OTP</label>
              <div style={{ position: 'relative' }}>
                <Hash size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input className="input" style={{ paddingLeft: '2rem', letterSpacing: '0.2em', fontFamily: 'var(--font-mono)' }}
                  type="text" placeholder="000000" maxLength={6}
                  value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g, ''))} required />
              </div>
            </div>
            <button type="submit" className="btn btn-primary w-full" disabled={loading || otp.length < 6}
              style={{ justifyContent: 'center' }}>
              {loading ? 'Verifying…' : 'Verify OTP'}
            </button>
            <button type="button" className="btn btn-outline w-full" style={{ justifyContent: 'center' }}
              onClick={() => setMode('otp-send')}>← Back</button>
          </form>
        )}

        <p style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1.5rem' }}>
          Default admin: admin@safeguard.local / admin1234
        </p>
      </div>
    </div>
  );
}
