import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { authApi } from '../api/client';

interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithOtp: (email: string, otp: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      authApi.me()
        .then(res => setUser(res.data))
        .catch(() => { setToken(null); localStorage.removeItem('token'); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const _saveToken = (t: string) => {
    localStorage.setItem('token', t);
    setToken(t);
    // User will be fetched via /me effect
  };

  const login = async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    _saveToken(res.data.access_token);
    const me = await authApi.me();
    setUser(me.data);
  };

  const loginWithOtp = async (email: string, otp: string) => {
    const res = await authApi.verifyOtp(email, otp);
    _saveToken(res.data.access_token);
    const me = await authApi.me();
    setUser(me.data);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, loginWithOtp, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
