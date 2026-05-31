export interface AuthUser {
  email: string;
  org_id: string;
  groups: string[];
  exp: number;
}

function decodeJwt(token: string): AuthUser | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = parts[1];
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const json = atob(base64);
    const data = JSON.parse(json);
    return {
      email: data.sub,
      org_id: data.org_id,
      groups: data.groups || [],
      exp: data.exp,
    };
  } catch {
    return null;
  }
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

export function setTokens(access: string, refresh: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function getUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  const token = getAccessToken();
  if (!token) return null;
  const user = decodeJwt(token);
  if (!user) return null;
  if (user.exp * 1000 < Date.now()) return null;
  return user;
}

export function isAdmin(): boolean {
  if (typeof window === 'undefined') return false;
  const user = getUser();
  if (!user) return false;
  return user.groups.includes('admin');
}

export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return getUser() !== null;
}
