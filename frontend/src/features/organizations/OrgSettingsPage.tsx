import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOrgStore } from '../../store/orgStore';
import { organizationsApi } from '../../api/organizations';
import { slugify } from '../../utils/formatters';
import toast from 'react-hot-toast';

export default function OrgSettingsPage() {
  const navigate = useNavigate();
  const { currentOrg, setCurrentOrg, setOrganizations } = useOrgStore();
  const [name, setName] = useState(currentOrg?.name || '');
  const [saving, setSaving] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newOrg, setNewOrg] = useState({ name: '', slug: '' });

  useEffect(() => {
    if (currentOrg) setName(currentOrg.name);
  }, [currentOrg?.id]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    setSaving(true);
    try {
      const res = await organizationsApi.update(currentOrg.id, { name });
      setCurrentOrg({ ...currentOrg, name: res.data.name });
      toast.success('Organization updated');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await organizationsApi.create({
        name: newOrg.name,
        slug: newOrg.slug || slugify(newOrg.name),
      });
      // Refresh orgs
      const orgsRes = await organizationsApi.list();
      setOrganizations(orgsRes.data);
      setCurrentOrg(res.data);
      setShowCreate(false);
      setNewOrg({ name: '', slug: '' });
      toast.success('Organization created!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create');
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Manage your organization</p>
        </div>
        <button className="btn btn-secondary" onClick={() => setShowCreate(true)} id="btn-create-org">
          + New Organization
        </button>
      </div>

      {currentOrg && (
        <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="card-header">
            <span className="card-title">Organization Details</span>
          </div>
          <div className="card-body">
            <form onSubmit={handleUpdate} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', maxWidth: 400 }}>
              <div className="form-group">
                <label className="form-label">Organization Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  id="org-name-input"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Slug</label>
                <input
                  type="text"
                  className="form-input"
                  value={currentOrg.slug}
                  disabled
                  style={{ opacity: 0.5 }}
                />
              </div>
              <button type="submit" className="btn btn-primary" disabled={saving} style={{ alignSelf: 'flex-start' }}>
                {saving ? <span className="loader" /> : 'Save Changes'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Create Org Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Create Organization</span>
              <button className="modal-close" onClick={() => setShowCreate(false)}>×</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                <div className="form-group">
                  <label className="form-label">Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Acme Corp"
                    value={newOrg.name}
                    onChange={(e) => setNewOrg({ ...newOrg, name: e.target.value, slug: slugify(e.target.value) })}
                    required
                    autoFocus
                    id="create-org-name"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Slug</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="acme-corp"
                    value={newOrg.slug}
                    onChange={(e) => setNewOrg({ ...newOrg, slug: e.target.value })}
                    pattern="^[a-z0-9\-]+$"
                    id="create-org-slug"
                  />
                  <span className="text-sm text-muted">Lowercase letters, numbers, and hyphens only</span>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" id="btn-submit-org">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
