import { cookies } from 'next/headers';

export const API_URL =
  process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = cookies().get('token')?.value;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const init: RequestInit = { ...options, headers };
  if (!options.cache && !(options as any).next) init.cache = 'no-store';

  const response = await fetch(`${API_URL}${endpoint}`, init);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(typeof err.detail === 'string' ? err.detail : `API request failed (${response.status})`);
  }
  return response.json();
}