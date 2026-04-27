import React, { useEffect, useState } from 'react';
import { useOrgStore } from '../../store/orgStore';
import { tasksApi } from '../../api/tasks';
import { organizationsApi } from '../../api/organizations';
import { formatDate, isOverdue, getInitials, getAvatarColor } from '../../utils/formatters';
import { canDeleteTasks } from '../../utils/permissions';
import type { Task, PaginatedResponse, TaskFilters, Member } from '../../types';
import toast from 'react-hot-toast';

export default function TaskListPage() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const [data, setData] = useState<PaginatedResponse<Task> | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [userRole, setUserRole] = useState('member');
  const [filters, setFilters] = useState<TaskFilters>({ page: 1, page_size: 20 });

  const fetchTasks = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const res = await tasksApi.list(currentOrg.id, filters);
      setData(res.data);
    } catch {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentOrg) return;
    fetchTasks();
    organizationsApi.listMembers(currentOrg.id).then((res) => {
      setMembers(res.data);
      // Find current user's role
      const authData = localStorage.getItem('taskforge-auth');
      if (authData) {
        const parsed = JSON.parse(authData);
        const userId = parsed?.state?.user?.id;
        const me = res.data.find((m: Member) => m.user_id === userId);
        if (me) setUserRole(me.role);
      }
    }).catch(() => {});
  }, [currentOrg?.id, filters]);

  // Create Task Modal
  const [newTask, setNewTask] = useState({
    title: '', description: '', priority: 'medium', assignee_id: '', due_date: ''
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    try {
      await tasksApi.create(currentOrg.id, {
        title: newTask.title,
        description: newTask.description || undefined,
        priority: newTask.priority,
        assignee_id: newTask.assignee_id || undefined,
        due_date: newTask.due_date || undefined,
      });
      toast.success('Task created!');
      setShowCreate(false);
      setNewTask({ title: '', description: '', priority: 'medium', assignee_id: '', due_date: '' });
      fetchTasks();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create task');
    }
  };

  const handleDelete = async (taskId: string) => {
    if (!currentOrg || !confirm('Delete this task?')) return;
    try {
      await tasksApi.delete(currentOrg.id, taskId);
      toast.success('Task deleted');
      fetchTasks();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const handleStatusChange = async (taskId: string, status: string) => {
    if (!currentOrg) return;
    try {
      await tasksApi.updateStatus(currentOrg.id, taskId, status);
      toast.success('Status updated');
      fetchTasks();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid status transition');
    }
  };

  if (!currentOrg) return null;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Tasks</h1>
          <p className="page-subtitle">{data?.total ?? 0} total tasks</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)} id="btn-create-task">
          + New Task
        </button>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-wrapper">
          <input
            type="text"
            className="search-input"
            placeholder="Search tasks..."
            value={filters.search || ''}
            onChange={(e) => setFilters({ ...filters, search: e.target.value || undefined, page: 1 })}
            id="task-search"
          />
        </div>
        <select
          className="filter-select"
          value={filters.status || ''}
          onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined, page: 1 })}
          id="filter-status"
        >
          <option value="">All Status</option>
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="in_review">In Review</option>
          <option value="done">Done</option>
        </select>
        <select
          className="filter-select"
          value={filters.priority || ''}
          onChange={(e) => setFilters({ ...filters, priority: e.target.value || undefined, page: 1 })}
          id="filter-priority"
        >
          <option value="">All Priority</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          className="filter-select"
          value={filters.assignee_id || ''}
          onChange={(e) => setFilters({ ...filters, assignee_id: e.target.value || undefined, page: 1 })}
          id="filter-assignee"
        >
          <option value="">All Assignees</option>
          {members.map((m) => (
            <option key={m.user_id} value={m.user_id}>{m.full_name}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="page-loader"><span className="loader loader-lg" /></div>
      ) : (data?.items?.length ?? 0) === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <div className="empty-state-title">No tasks found</div>
          <div className="empty-state-text">Create your first task to get started.</div>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Assignee</th>
                    <th>Due Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((task) => (
                    <tr key={task.id}>
                      <td>
                        <div style={{ fontWeight: 500 }}>{task.title}</div>
                        {task.description && (
                          <div className="text-sm text-muted truncate" style={{ maxWidth: 300 }}>
                            {task.description}
                          </div>
                        )}
                      </td>
                      <td>
                        <select
                          className="filter-select"
                          value={task.status}
                          onChange={(e) => handleStatusChange(task.id, e.target.value)}
                          style={{ minWidth: 120 }}
                        >
                          <option value="todo">To Do</option>
                          <option value="in_progress">In Progress</option>
                          <option value="in_review">In Review</option>
                          <option value="done">Done</option>
                        </select>
                      </td>
                      <td>
                        <span className={`badge badge-${task.priority}`}>
                          {task.priority}
                        </span>
                      </td>
                      <td>
                        {task.assignee_name ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                            <div
                              className="avatar avatar-sm"
                              style={{ background: getAvatarColor(task.assignee_name), color: '#fff' }}
                            >
                              {getInitials(task.assignee_name)}
                            </div>
                            <span className="text-sm">{task.assignee_name}</span>
                          </div>
                        ) : (
                          <span className="text-muted text-sm">Unassigned</span>
                        )}
                      </td>
                      <td>
                        <span style={{ color: isOverdue(task.due_date) && task.status !== 'done' ? 'var(--color-error)' : 'inherit' }}>
                          {formatDate(task.due_date)}
                        </span>
                      </td>
                      <td>
                        {canDeleteTasks(userRole) && (
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => handleDelete(task.id)}
                            title="Delete task"
                          >
                            🗑️
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="pagination">
              <span className="pagination-info">
                Page {data.page} of {data.total_pages} ({data.total} results)
              </span>
              <div className="pagination-controls">
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={data.page <= 1}
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                >
                  ← Previous
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={data.page >= data.total_pages}
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Create Task Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Create New Task</span>
              <button className="modal-close" onClick={() => setShowCreate(false)}>×</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                <div className="form-group">
                  <label className="form-label">Title *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="What needs to be done?"
                    value={newTask.title}
                    onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                    required
                    autoFocus
                    id="new-task-title"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-input form-textarea"
                    placeholder="Add details..."
                    value={newTask.description}
                    onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                    id="new-task-desc"
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
                  <div className="form-group">
                    <label className="form-label">Priority</label>
                    <select
                      className="form-input form-select"
                      value={newTask.priority}
                      onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                      id="new-task-priority"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Due Date</label>
                    <input
                      type="date"
                      className="form-input"
                      value={newTask.due_date}
                      onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                      id="new-task-due"
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Assignee</label>
                  <select
                    className="form-input form-select"
                    value={newTask.assignee_id}
                    onChange={(e) => setNewTask({ ...newTask, assignee_id: e.target.value })}
                    id="new-task-assignee"
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => (
                      <option key={m.user_id} value={m.user_id}>{m.full_name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" id="btn-submit-task">Create Task</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
