/* ============================================================
   TypeScript type definitions for TaskForge
   ============================================================ */

// --- Auth ---
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: TokenResponse;
}

// --- Organization ---
export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_by: string;
  created_at: string;
  member_count?: number;
}

export interface Member {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
}

// --- Task ---
export type TaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id: string | null;
  assignee_name: string | null;
  created_by: string;
  creator_name: string | null;
  due_date: string | null;
  position: number;
  org_id: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskFilters {
  status?: string;
  priority?: string;
  assignee_id?: string;
  due_before?: string;
  due_after?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

// --- Invite ---
export interface Invite {
  id: string;
  email: string;
  role: string;
  status: string;
  invited_by: string;
  inviter_name: string | null;
  expires_at: string;
  created_at: string;
  org_id: string;
  token?: string;
}

// --- Analytics ---
export interface TaskStatsOverview {
  total_tasks: number;
  todo_count: number;
  in_progress_count: number;
  in_review_count: number;
  done_count: number;
  overdue_count: number;
  total_members: number;
}

export interface UserPerformance {
  user_id: string;
  full_name: string;
  email: string;
  tasks_assigned: number;
  tasks_completed: number;
  completion_rate: number;
}

export interface ActivityEntry {
  id: string;
  user_id: string;
  user_name: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  changes: Record<string, unknown> | null;
  created_at: string;
}
