import apiClient from './client';
import type { AuthResponse, TokenResponse, User } from '../types';

export const authApi = {
  register: (data: { email: string; full_name: string; password: string }) =>
    apiClient.post<AuthResponse>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<AuthResponse>('/auth/login', data),

  refresh: (refresh_token: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', { refresh_token }),

  getMe: () =>
    apiClient.get<User>('/auth/me'),
};
