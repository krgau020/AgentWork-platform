import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from './auth';

const BASE = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000';

export interface UserResponse {
  user_id: string;
  email: string;
  org_id: string;
  is_active: boolean;
}

export interface GroupResponse {
  group_id: string;
  name: string;
  org_id: string;
}

export interface StatementResponse {
  statement_id: string;
  resource: string;
  action: string;
  effect: 'allow' | 'deny';
}

export interface PolicyResponse {
  policy_id: string;
  name: string;
  org_id: string;
  statements: StatementResponse[];
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface OrgResponse {
  org_id: string;
  name: string;
}

export interface ServiceResponse {
  service_id: string;
  name: string;
  display_name: string;
  base_url: string;
  route_prefix: string;
  allowed_groups: string[];
  health_endpoint: string;
  is_active: boolean;
  registered_at: string | null;
}

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const isRefreshCall = path.includes('/auth/refresh');

  const accessToken = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401 && !isRefreshCall) {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      window.location.href = '/login';
      return res;
    }

    const refreshRes = await fetch(`${BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!refreshRes.ok) {
      clearTokens();
      window.location.href = '/login';
      return res;
    }

    const refreshData = await refreshRes.json();
    setTokens(refreshData.access_token, refreshData.refresh_token);

    const retryHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
      Authorization: `Bearer ${refreshData.access_token}`,
    };

    return fetch(`${BASE}${path}`, { ...options, headers: retryHeaders });
  }

  return res;
}

export const api = {
  // Auth — public routes (no token needed)
  login(email: string, password: string): Promise<Response> {
    return fetch(`${BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  },

  signup(email: string, password: string, org_name: string): Promise<Response> {
    return fetch(`${BASE}/api/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, org_name }),
    });
  },

  acceptInvite(invite_token: string, password: string): Promise<Response> {
    return fetch(`${BASE}/api/v1/auth/accept-invite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invite_token, password }),
    });
  },

  logout(refresh_token: string): Promise<Response> {
    return apiFetch('/api/v1/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token }),
    });
  },

  // Users
  async listUsers(page = 1, limit = 10): Promise<PaginatedResponse<UserResponse>> {
    const res = await apiFetch(`/api/v1/users?page=${page}&limit=${limit}`);
    return res.json();
  },

  async getUser(userId: string): Promise<UserResponse> {
    const res = await apiFetch(`/api/v1/users/${userId}`);
    return res.json();
  },

  async getUserGroups(userId: string): Promise<GroupResponse[]> {
    const res = await apiFetch(`/api/v1/users/${userId}/groups`);
    return res.json();
  },

  addUserToGroup(userId: string, groupId: string): Promise<Response> {
    return apiFetch(`/api/v1/users/${userId}/groups`, {
      method: 'POST',
      body: JSON.stringify({ group_id: groupId }),
    });
  },

  removeUserFromGroup(userId: string, groupId: string): Promise<Response> {
    return apiFetch(`/api/v1/users/${userId}/groups/${groupId}`, {
      method: 'DELETE',
    });
  },

  // Groups
  async listGroups(page = 1, limit = 10): Promise<PaginatedResponse<GroupResponse>> {
    const res = await apiFetch(`/api/v1/groups?page=${page}&limit=${limit}`);
    return res.json();
  },

  createGroup(name: string): Promise<Response> {
    return apiFetch('/api/v1/groups', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  assignPolicyToGroup(groupId: string, policyId: string): Promise<Response> {
    return apiFetch(`/api/v1/groups/${groupId}/policies`, {
      method: 'POST',
      body: JSON.stringify({ policy_id: policyId }),
    });
  },

  removePolicyFromGroup(groupId: string, policyId: string): Promise<Response> {
    return apiFetch(`/api/v1/groups/${groupId}/policies/${policyId}`, {
      method: 'DELETE',
    });
  },

  // Policies
  async listPolicies(page = 1, limit = 10): Promise<PaginatedResponse<PolicyResponse>> {
    const res = await apiFetch(`/api/v1/policies?page=${page}&limit=${limit}`);
    return res.json();
  },

  createPolicy(name: string): Promise<Response> {
    return apiFetch('/api/v1/policies', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  updatePolicy(policyId: string, name: string): Promise<Response> {
    return apiFetch(`/api/v1/policies/${policyId}`, {
      method: 'PUT',
      body: JSON.stringify({ name }),
    });
  },

  addStatement(
    policyId: string,
    resource: string,
    action: string,
    effect: string
  ): Promise<Response> {
    return apiFetch(`/api/v1/policies/${policyId}/statements`, {
      method: 'POST',
      body: JSON.stringify({ resource, action, effect }),
    });
  },

  updateStatement(
    policyId: string,
    statementId: string,
    resource: string,
    action: string,
    effect: string
  ): Promise<Response> {
    return apiFetch(`/api/v1/policies/${policyId}/statements/${statementId}`, {
      method: 'PUT',
      body: JSON.stringify({ resource, action, effect }),
    });
  },

  removeStatement(policyId: string, statementId: string): Promise<Response> {
    return apiFetch(`/api/v1/policies/${policyId}/statements/${statementId}`, {
      method: 'DELETE',
    });
  },

  // Orgs
  async getOrg(orgId: string): Promise<OrgResponse> {
    const res = await apiFetch(`/api/v1/orgs/${orgId}`);
    return res.json();
  },

  // Invites
  createInvite(orgId: string, email: string, groupId: string): Promise<Response> {
    return apiFetch(`/api/v1/orgs/${orgId}/invites`, {
      method: 'POST',
      body: JSON.stringify({ email, group_id: groupId }),
    });
  },

  // Solutions
  async listSolutions(): Promise<ServiceResponse[]> {
    const res = await apiFetch('/api/v1/solutions');
    return res.json();
  },

  chatWithSolution(serviceName: string, message: string): Promise<Response> {
    return apiFetch(`/api/v1/solutions/${serviceName}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
};
