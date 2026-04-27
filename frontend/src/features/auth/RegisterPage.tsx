import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../api/auth';
import { useAuthStore } from '../../store/authStore';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: '', full_name: '', password: '', confirm: '' });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirm) {
      setError('Passwords do not match.');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    setLoading(true);
    try {
      const res = await authApi.register({
        email: form.email,
        full_name: form.full_name,
        password: form.password,
      });
      const { user, tokens } = res.data;
      login(user, tokens.access_token, tokens.refresh_token);
      toast.success('Account created! Welcome to TaskForge.');
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  // Password strength
  const getStrength = (pw: string) => {
    if (pw.length === 0) return { level: 0, label: '' };
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
    const colors = ['', '#ef4444', '#f59e0b', '#3b82f6', '#10b981'];
    return { level: score, label: labels[score], color: colors[score] };
  };

  const strength = getStrength(form.password);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">T</div>
          <span className="auth-logo-text">TaskForge</span>
        </div>

        <div className="auth-heading">
          <h1>Create your account</h1>
          <p>Start managing tasks with your team</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="form-error" style={{ textAlign: 'center', padding: '8px', background: 'var(--color-error-bg)', borderRadius: 'var(--radius-md)' }}>
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="reg-name">Full Name</label>
            <input
              id="reg-name"
              type="text"
              className="form-input"
              placeholder="John Doe"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-email">Email</label>
            <input
              id="reg-email"
              type="email"
              className="form-input"
              placeholder="you@company.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              type="password"
              className="form-input"
              placeholder="Min. 8 characters"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
            {form.password && (
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center', marginTop: '4px' }}>
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      height: '3px',
                      borderRadius: '2px',
                      background: i <= strength.level ? strength.color : 'var(--color-border)',
                      transition: 'background 200ms',
                    }}
                  />
                ))}
                <span style={{ fontSize: '11px', color: strength.color, marginLeft: '8px', fontWeight: 500 }}>
                  {strength.label}
                </span>
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="reg-confirm">Confirm Password</label>
            <input
              id="reg-confirm"
              type="password"
              className="form-input"
              placeholder="Re-enter password"
              value={form.confirm}
              onChange={(e) => setForm({ ...form, confirm: e.target.value })}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
            {loading ? <span className="loader" /> : 'Create Account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account?{' '}
          <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
