import React, { useEffect, useState } from 'react';
import { useOrgStore } from '../../store/orgStore';
import { organizationsApi } from '../../api/organizations';
import { formatDate } from '../../utils/formatters';
import type { Invite } from '../../types';
import toast from 'react-hot-toast';

export default function InvitePage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ email: '', role: 'member' });
  const [sending, setSending] = useState(false);

  const fetchInvites = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const res = await organizationsApi.listInvites(currentOrg.id);
      setInvites(res.data);
    } catch {} finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchInvites(); }, [currentOrg?.id]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    setSending(true);
    try {
      const res = await organizationsApi.createInvite(currentOrg.id, form);
      toast.success(`Invite sent to ${form.email}`);
      setForm({ email: '', role: 'member' });
      fetchInvites();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to send invite');
    } finally {
      setSending(false);
    }
  };

  const handleRevoke = async (inviteId: string) => {
    if (!currentOrg || !confirm('Revoke this invite?')) return;
    try {
      await organizationsApi.revokeInvite(currentOrg.id, inviteId);
      toast.success('Invite revoked');
      fetchInvites();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to revoke');
    }
  };

  if (!currentOrg) return null;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Invites</h1>
          <p className="page-subtitle">Invite new members to {currentOrg.name}</p>
        </div>
      </div>

      {/* Invite Form */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="card-header">
          <span className="card-title">Send Invite</span>
        </div>
        <div className="card-body">
          <form onSubmit={handleInvite} style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
              <label className="form-label" htmlFor="invite-email">Email Address</label>
              <input
                id="invite-email"
                type="email"
                className="form-input"
                placeholder="colleague@company.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div className="form-group" style={{ width: 140 }}>
              <label className="form-label" htmlFor="invite-role">Role</label>
              <select
                id="invite-role"
                className="form-input form-select"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button type="submit" className="btn btn-primary" disabled={sending} id="btn-send-invite">
              {sending ? <span className="loader" /> : 'Send Invite'}
            </button>
          </form>
        </div>
      </div>

      {/* Pending Invites */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Pending Invites ({invites.length})</span>
        </div>
        {loading ? (
          <div className="card-body">
            <div className="page-loader"><span className="loader" /></div>
          </div>
        ) : invites.length === 0 ? (
          <div className="card-body">
            <div className="empty-state" style={{ padding: 'var(--space-8)' }}>
              <div className="empty-state-icon">📨</div>
              <div className="empty-state-title">No pending invites</div>
              <div className="empty-state-text">Send an invite above to grow your team.</div>
            </div>
          </div>
        ) : (
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Invited By</th>
                  <th>Expires</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invites.map((inv) => (
                  <tr key={inv.id}>
                    <td style={{ fontWeight: 500 }}>{inv.email}</td>
                    <td><span className={`badge badge-${inv.role}`}>{inv.role}</span></td>
                    <td className="text-sm text-muted">{inv.inviter_name || '—'}</td>
                    <td className="text-sm">{formatDate(inv.expires_at)}</td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleRevoke(inv.id)}>
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
