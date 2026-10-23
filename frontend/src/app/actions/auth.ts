'use server'

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { revalidatePath } from 'next/cache';
import { API_URL } from '@/lib/api-client';

export type FormState = { error?: string; ok?: boolean } | null;

function errorText(body: any, fallback: string) {
  const d = body?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((e: any) => e.msg).join('; ');
  return fallback;
}

function setSession(token: string) {
  cookies().set('token', token, {
    httpOnly: true, secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax', maxAge: 60 * 60 * 24, path: '/',
  });
}

export async function loginAction(_prev: FormState, formData: FormData): Promise<FormState> {
  const params = new URLSearchParams();
  params.append('username', String(formData.get('email') ?? ''));
  params.append('password', String(formData.get('password') ?? ''));
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
  if (!res.ok) return { error: errorText(await res.json().catch(() => ({})), 'Login failed') };
  setSession((await res.json()).access_token);
  redirect('/dashboard');
}

export async function registerAction(_prev: FormState, formData: FormData): Promise<FormState> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: formData.get('email'), password: formData.get('password') }),
  });
  if (!res.ok) return { error: errorText(await res.json().catch(() => ({})), 'Registration failed') };
  setSession((await res.json()).access_token);
  redirect('/dashboard/preferences');
}

export async function logoutAction() {
  cookies().delete('token');
  redirect('/login');
}

const list = (v: FormDataEntryValue | null) =>
  String(v ?? '').split(',').map((s) => s.trim()).filter(Boolean);

export async function savePreferencesAction(_prev: FormState, formData: FormData): Promise<FormState> {
  const token = cookies().get('token')?.value;
  const res = await fetch(`${API_URL}/preferences`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      target_roles: list(formData.get('target_roles')),
      preferred_countries: list(formData.get('preferred_countries')),
      skills: list(formData.get('skills')),
      alert_frequency: formData.get('alert_frequency'),
      min_relevance_score: Number(formData.get('min_relevance_score') ?? 50),
    }),
  });
  if (!res.ok) return { error: errorText(await res.json().catch(() => ({})), 'Save failed') };
  revalidatePath('/dashboard/preferences');
  return { ok: true };
}

export async function triggerScrapeAction(sourceId: number): Promise<FormState> {
  const token = cookies().get('token')?.value;
  const res = await fetch(`${API_URL}/admin/sources/${sourceId}/trigger`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return { error: errorText(await res.json().catch(() => ({})), 'Trigger failed') };
  revalidatePath('/dashboard/admin');
  return { ok: true };
}