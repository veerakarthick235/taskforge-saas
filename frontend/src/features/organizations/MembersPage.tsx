import React, { useEffect, useState } from 'react';
import { useOrgStore } from '../../store/orgStore';
import { organizationsApi } from '../../api/organizations';
import { getInitials, getAvatarColor } from '../../utils/formatters';
import { canManageMembers, canChangeRoles } from '../../utils/permissions';
import type { Member } from '../../types';
import toast from 'react-hot-toast';

export default function MembersPage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [myRole, setMyRole] = useState('member');

  const fetchMembers = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const res = await organizationsApi.listMembers(currentOrg.id);
      setMembers(res.data);
      // Find my role
      const authData = localStorage.getItem('taskforge-auth');
      if (authData) {
        const parsed = JSON.parse(authData);
        const userId = parsed?.state?.user?.id;
        const me = res.data.find((m: Member) => m.user_id === userId);
        if (me) setMyRole(me.role);
      }
    } catch {} finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMembers(); }, [currentOrg?.id]);

  const handleRemove = async (userId: string, name: string) => {
    if (!currentOrg || !confirm(`Remove ${name} from the organization?`)) return;
    try {
      await organizationsApi.removeMember(currentOrg.id, userId);
      toast.success('Member removed');
      fetchMembers();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to remove');
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    if (!currentOrg) return;
    try {
      await organizationsApi.updateMemberRole(currentOrg.id, userId, newRole);
      toast.success('Role updated');
      fetchMembers();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to change role');
    }
  };

  if (!currentOrg) return null;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Members</h1>
          <p className="page-subtitle">{members.length} members in {currentOrg.name}</p>
        </div>
      </div>

      {loading ? (
        <div className="page-loader"><span className="loader loader-lg" /></div>
      ) : (
        <div className="card">
          {members.map((member) => (
            <div className="member-row" key={member.id}>
              <div className="member-info">
                <div
                  className="avatar avatar-md"
                  style={{ background: getAvatarColor(member.full_name), color: '#fff' }}
                >
                  {getInitials(member.full_name)}
                </div>
                <div className="member-details">
                  <span className="member-name">{member.full_name}</span>
                  <span className="member-email">{member.email}</span>
                </div>
              </div>
              <div className="member-actions">
                <span className={`badge badge-${member.role}`}>{member.role}</span>

                {canChangeRoles(myRole) && member.role !== 'owner' && (
                  <select
                    className="filter-select"
                    value={member.role}
                    onChange={(e) => handleRoleChange(member.user_id, e.target.value)}
                    style={{ minWidth: 100 }}
                  >
                    <option value="admin">Admin</option>
                    <option value="member">Member</option>
                  </select>
                )}

                {canManageMembers(myRole) && member.role !== 'owner' && (
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleRemove(member.user_id, member.full_name)}
                    title="Remove member"
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
