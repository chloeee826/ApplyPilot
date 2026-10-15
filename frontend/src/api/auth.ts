import { apiFetch, parseResponse } from './client'

export interface User { id: string; email: string }

export async function currentUser(): Promise<User | null> {
  const response = await apiFetch('/api/auth/me')
  if (response.status === 401) return null
  return parseResponse<User>(response)
}

export async function signIn(mode: 'login' | 'register', email: string, password: string): Promise<User> {
  return parseResponse<User>(await apiFetch(`/api/auth/${mode}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }),
  }))
}

export async function signOut(): Promise<void> {
  const response = await apiFetch('/api/auth/logout', { method: 'POST' })
  if (!response.ok) throw new Error('Could not sign out. Please try again.')
}
