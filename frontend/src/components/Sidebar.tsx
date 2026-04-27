import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useOrgStore } from '../store/orgStore';
import OrgSwitcher from '../features/organizations/OrgSwitcher';

export default function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const currentOrg = useOrgStore((s) => s.currentOrg);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar" id="app-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">T</div>
        <span className="sidebar-brand">TaskForge</span>
      </div>

      <nav className="sidebar-nav">
        {/* Org Switcher */}
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <OrgSwitcher />
        </div>

        <span className="sidebar-section-label">Main</span>
        <NavLink to="/" end className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} id="nav-dashboard">
          <span className="sidebar-link-icon">📊</span>
          Dashboard
        </NavLink>
        <NavLink to="/tasks" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} id="nav-tasks">
          <span className="sidebar-link-icon">✅</span>
          Tasks
        </NavLink>
        <NavLink to="/board" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} id="nav-board">
          <span className="sidebar-link-icon">📋</span>
          Board
        </NavLink>

        <span className="sidebar-section-label">Organization</span>
        <NavLink to="/members" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} id="nav-members">
          <span className="sidebar-link-icon">👥</span>
          Members
        </NavLink>
        <NavLink to="/invites" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} id="nav-invites">
          <span className="sidebar-link-icon">📨</span>
          Invites
        </NavLink>
        <NavLink to="/settings" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} id="nav-settings">
          <span className="sidebar-link-icon">⚙️</span>
          Settings
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0 }}>
            <div className="avatar avatar-sm" style={{ background: '#6366f1', color: '#fff', fontSize: '11px' }}>
              {user?.full_name?.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)}
            </div>
            <div style={{ minWidth: 0 }}>
              <div className="truncate" style={{ fontSize: 'var(--font-size-sm)', fontWeight: 500 }}>{user?.full_name}</div>
              <div className="truncate" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{user?.email}</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={handleLogout} id="btn-logout" title="Sign out">
            🚪
          </button>
        </div>
      </div>
    </aside>
  );
}
