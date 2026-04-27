import React, { useEffect, useState } from 'react';
import { useOrgStore } from '../../store/orgStore';
import { organizationsApi } from '../../api/organizations';
import { formatRelativeTime } from '../../utils/formatters';
import type { TaskStatsOverview, ActivityEntry } from '../../types';

export default function DashboardPage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const [stats, setStats] = useState<TaskStatsOverview | null>(null);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentOrg) return;

    setLoading(true);
    Promise.all([
      organizationsApi.getOverview(currentOrg.id),
      organizationsApi.getActivityFeed(currentOrg.id),
    ])
      .then(([statsRes, activityRes]) => {
        setStats(statsRes.data);
        setActivity(activityRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [currentOrg?.id]);

  if (!currentOrg) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <div className="empty-state-icon">🏢</div>
          <div className="empty-state-title">No Organization Selected</div>
          <div className="empty-state-text">
            Create or join an organization to get started with TaskForge.
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="page-loader"><span className="loader loader-lg" /></div>
      </div>
    );
  }

  const statCards = [
    { label: 'Total Tasks', value: stats?.total_tasks ?? 0, accent: 'var(--color-accent)' },
    { label: 'To Do', value: stats?.todo_count ?? 0, accent: 'var(--color-status-todo)' },
    { label: 'In Progress', value: stats?.in_progress_count ?? 0, accent: 'var(--color-status-in-progress)' },
    { label: 'In Review', value: stats?.in_review_count ?? 0, accent: 'var(--color-status-in-review)' },
    { label: 'Done', value: stats?.done_count ?? 0, accent: 'var(--color-status-done)' },
    { label: 'Overdue', value: stats?.overdue_count ?? 0, accent: 'var(--color-error)' },
    { label: 'Team Members', value: stats?.total_members ?? 0, accent: '#8b5cf6' },
  ];

  const formatAction = (entry: ActivityEntry) => {
    const actions: Record<string, string> = {
      created: 'created',
      updated: 'updated',
      deleted: 'deleted',
      status_changed: 'changed status of',
      assigned: 'assigned',
      invited: 'invited someone to',
      accepted_invite: 'joined',
      removed_member: 'removed a member from',
      changed_role: 'changed role in',
    };
    return `${actions[entry.action] || entry.action} a ${entry.entity_type}`;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">{currentOrg.name} — Overview</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid" style={{ marginBottom: 'var(--space-8)' }}>
        {statCards.map((s) => (
          <div
            key={s.label}
            className="stat-card"
            style={{ '--stat-accent': s.accent } as React.CSSProperties}
          >
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Activity Feed */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Activity</span>
        </div>
        <div className="card-body">
          {activity.length === 0 ? (
            <div className="empty-state" style={{ padding: 'var(--space-8)' }}>
              <div className="empty-state-icon">📭</div>
              <div className="empty-state-title">No activity yet</div>
              <div className="empty-state-text">Actions will appear here as your team works.</div>
            </div>
          ) : (
            activity.slice(0, 15).map((entry) => (
              <div className="activity-item" key={entry.id}>
                <div className="activity-dot" />
                <div className="activity-content">
                  <div className="activity-text">
                    <strong>{entry.user_name}</strong> {formatAction(entry)}
                  </div>
                  <div className="activity-time">{formatRelativeTime(entry.created_at)}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
