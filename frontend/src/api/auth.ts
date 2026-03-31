import { UserInfo } from '../types';
import { apiFetch } from './client';

export async function login(username: string, password: string): Promise<string> {
  const data = await apiFetch<{ access_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  localStorage.setItem('mn_token', data.access_token);
  return data.access_token;
}

export async function getMe(): Promise<UserInfo> {
  return apiFetch<UserInfo>('/auth/me');
}

export function logout() {
  localStorage.removeItem('mn_token');
  window.location.href = '/admin/login';
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem('mn_token');
}
