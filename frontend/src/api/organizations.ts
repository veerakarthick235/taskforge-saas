import apiClient from './client';
import type {
  Organization,
  Member,
  Invite,
  TaskStatsOverview,
  UserPerformance,
  ActivityEntry,
} from '../types';

export const organizationsApi = {
  list: () =>
    apiClient.get<Organization[]>('/organizations/'),

  get: (orgId: string) =>
    apiClient.get<Organization>(`/organizations/${orgId}`),

  create: (data: { name: string; slug: string }) =>
    apiClient.post<Organization>('/organizations/', data),

  update: (orgId: string, data: { name?: string }) =>
    apiClient.patch<Organization>(`/organizations/${orgId}`, data),

  // Members
  listMembers: (orgId: string) =>
    apiClient.get<Member[]>(`/organizations/${orgId}/members`),

  removeMember: (orgId: string, userId: string) =>
    apiClient.delete(`/organizations/${orgId}/members/${userId}`),

  updateMemberRole: (orgId: string, userId: string, role: string) =>
    apiClient.patch<Member>(`/organizations/${orgId}/members/${userId}/role`, { role }),

  // Invites
  listInvites: (orgId: string) =>
    apiClient.get<Invite[]>(`/organizations/${orgId}/invites/`),

  createInvite: (orgId: string, data: { email: string; role?: string }) =>
    apiClient.post<Invite>(`/organizations/${orgId}/invites/`, data),

  revokeInvite: (orgId: string, inviteId: string) =>
    apiClient.delete(`/organizations/${orgId}/invites/${inviteId}`),

  acceptInvite: (token: string) =>
    apiClient.post('/invites/accept', { token }),

  // Analytics
  getOverview: (orgId: string) =>
    apiClient.get<TaskStatsOverview>(`/organizations/${orgId}/analytics/overview`),

  getUserPerformance: (orgId: string) =>
    apiClient.get<UserPerformance[]>(`/organizations/${orgId}/analytics/user-performance`),

  getActivityFeed: (orgId: string, page: number = 1) =>
    apiClient.get<ActivityEntry[]>(`/organizations/${orgId}/analytics/activity-feed`, {
      params: { page },
    }),
};
