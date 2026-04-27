import React, { useEffect, useState } from 'react';
import { useOrgStore } from '../../store/orgStore';
import { tasksApi } from '../../api/tasks';
import { getInitials, getAvatarColor, isOverdue, formatDate } from '../../utils/formatters';
import type { Task, TaskStatus } from '../../types';
import toast from 'react-hot-toast';

const COLUMNS: { key: TaskStatus; label: string; color: string }[] = [
  { key: 'todo', label: 'To Do', color: 'var(--color-status-todo)' },
  { key: 'in_progress', label: 'In Progress', color: 'var(--color-status-in-progress)' },
  { key: 'in_review', label: 'In Review', color: 'var(--color-status-in-review)' },
  { key: 'done', label: 'Done', color: 'var(--color-status-done)' },
];

export default function TaskBoardView() {
  const currentOrg = useOrgStore((s) => s.currentOrg);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentOrg) return;
    setLoading(true);
    tasksApi
      .list(currentOrg.id, { page_size: 200 })
      .then((res) => setTasks(res.data.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [currentOrg?.id]);

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    if (!currentOrg) return;
    try {
      await tasksApi.updateStatus(currentOrg.id, taskId, newStatus);
      // Update locally
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: newStatus as TaskStatus } : t))
      );
      toast.success('Status updated');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid transition');
    }
  };

  if (!currentOrg) return null;

  if (loading) {
    return (
      <div className="page-container">
        <div className="page-loader"><span className="loader loader-lg" /></div>
      </div>
    );
  }

  const grouped = COLUMNS.map((col) => ({
    ...col,
    tasks: tasks.filter((t) => t.status === col.key),
  }));

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Board</h1>
          <p className="page-subtitle">Kanban view of all tasks</p>
        </div>
      </div>

      <div className="task-board">
        {grouped.map((col) => (
          <div className="task-column" key={col.key}>
            <div className="task-column-header">
              <div className="task-column-title">
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: col.color, display: 'inline-block' }} />
                {col.label}
              </div>
              <span className="task-column-count">{col.tasks.length}</span>
            </div>
            <div className="task-column-body">
              {col.tasks.length === 0 ? (
                <div style={{ padding: 'var(--space-8) var(--space-4)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                  No tasks
                </div>
              ) : (
                col.tasks.map((task) => (
                  <div className="task-card" key={task.id}>
                    <div className="task-card-title">{task.title}</div>
                    <div className="task-card-meta">
                      <div className="task-card-tags">
                        <span className={`badge badge-${task.priority}`}>
                          {task.priority}
                        </span>
                        {task.due_date && (
                          <span style={{
                            fontSize: 'var(--font-size-xs)',
                            color: isOverdue(task.due_date) && task.status !== 'done'
                              ? 'var(--color-error)' : 'var(--color-text-muted)',
                          }}>
                            {formatDate(task.due_date)}
                          </span>
                        )}
                      </div>
                      {task.assignee_name && (
                        <div
                          className="avatar avatar-sm"
                          style={{ background: getAvatarColor(task.assignee_name), color: '#fff' }}
                          title={task.assignee_name}
                        >
                          {getInitials(task.assignee_name)}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
