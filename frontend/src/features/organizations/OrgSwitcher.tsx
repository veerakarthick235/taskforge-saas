import React, { useState, useEffect, useRef } from 'react';
import { useOrgStore } from '../../store/orgStore';
import { organizationsApi } from '../../api/organizations';
import { getInitials, getAvatarColor } from '../../utils/formatters';
import type { Organization } from '../../types';

export default function OrgSwitcher() {
  const { currentOrg, organizations, setCurrentOrg, setOrganizations } = useOrgStore();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    organizationsApi.list().then((res) => {
      setOrganizations(res.data);
    }).catch(() => {});
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSwitch = (org: Organization) => {
    setCurrentOrg(org);
    setOpen(false);
    // Reload page data when switching org
    window.location.reload();
  };

  if (!currentOrg) return null;

  return (
    <div className="org-switcher" ref={ref}>
      <button className="org-switcher-btn" onClick={() => setOpen(!open)} id="org-switcher-toggle">
        <div
          className="avatar avatar-sm"
          style={{ background: getAvatarColor(currentOrg.name), color: '#fff' }}
        >
          {getInitials(currentOrg.name)}
        </div>
        <span className="truncate" style={{ flex: 1 }}>{currentOrg.name}</span>
        <span style={{ fontSize: '10px', opacity: 0.5 }}>▼</span>
      </button>

      {open && (
        <div className="org-switcher-dropdown">
          {organizations.map((org) => (
            <button
              key={org.id}
              className={`org-switcher-item ${org.id === currentOrg.id ? 'active' : ''}`}
              onClick={() => handleSwitch(org)}
              id={`org-switch-${org.slug}`}
            >
              <div
                className="avatar avatar-sm"
                style={{ background: getAvatarColor(org.name), color: '#fff' }}
              >
                {getInitials(org.name)}
              </div>
              <span className="truncate">{org.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
