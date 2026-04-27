import apiClient from './client';
import type { Task, PaginatedResponse, TaskFilters } from '../types';

export const tasksApi = {
  list: (orgId: string, filters?: TaskFilters) =>
    apiClient.get<PaginatedResponse<Task>>(`/organizations/${orgId}/tasks/`, {
      params: filters,
    }),

  get: (orgId: string, taskId: string) =>
    apiClient.get<Task>(`/organizations/${orgId}/tasks/${taskId}`),

  create: (orgId: string, data: {
    title: string;
    description?: string;
    priority?: string;
    assignee_id?: string;
    due_date?: string;
  }) =>
    apiClient.post<Task>(`/organizations/${orgId}/tasks/`, data),

  update: (orgId: string, taskId: string, data: Partial<{
    title: string;
    description: string;
    priority: string;
    assignee_id: string;
    due_date: string;
  }>) =>
    apiClient.patch<Task>(`/organizations/${orgId}/tasks/${taskId}`, data),

  updateStatus: (orgId: string, taskId: string, status: string) =>
    apiClient.patch<Task>(`/organizations/${orgId}/tasks/${taskId}/status`, { status }),

  assign: (orgId: string, taskId: string, assignee_id: string | null) =>
    apiClient.patch<Task>(`/organizations/${orgId}/tasks/${taskId}/assign`, { assignee_id }),

  delete: (orgId: string, taskId: string) =>
    apiClient.delete(`/organizations/${orgId}/tasks/${taskId}`),
};
