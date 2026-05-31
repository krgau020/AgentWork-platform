'use client';

import { useEffect, useState, FormEvent } from 'react';
import { api } from '@/lib/api';
import { isAdmin, getUser } from '@/lib/auth';
import type { GroupResponse } from '@/lib/api';

interface InviteResult {
  invite_token: string;
  email: string;
  org_id: string;
  expires_at: string;
}

export default function InvitesPage() {
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [email, setEmail] = useState('');
  const [groupId, setGroupId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<InviteResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [groupsLoading, setGroupsLoading] = useState(true);

  const admin = isAdmin();
  const user = getUser();

  useEffect(() => {
    if (!admin) return;

    async function loadGroups() {
      setGroupsLoading(true);
      try {
        const data = await api.listGroups(1, 100);
        setGroups(data.data);
      } catch {
        setError('Failed to load groups');
      } finally {
        setGroupsLoading(false);
      }
    }

    loadGroups();
  }, [admin]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!user) return;
    setError('');
    setResult(null);
    setLoading(true);

    try {
      const res = await api.createInvite(user.org_id, email, groupId);
      if (!res.ok) {
        const d = await res.json();
        setError(d.message || 'Something went wrong');
        return;
      }
      const data: InviteResult = await res.json();
      setResult(data);
      setEmail('');
      setGroupId('');
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopyToken() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.invite_token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard not available
    }
  }

  async function handleCopyLink() {
    if (!result) return;
    try {
      const link = `${window.location.origin}/invite?token=${result.invite_token}`;
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard not available
    }
  }

  if (!admin) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-zinc-900">Invites</h1>
        <div className="mt-6 bg-white rounded-xl border border-zinc-200 shadow-sm px-6 py-10 text-center">
          <p className="text-zinc-500 text-sm">
            Only admins can create invitations.
          </p>
        </div>
      </div>
    );
  }

  const inviteLink = result
    ? `${typeof window !== 'undefined' ? window.location.origin : ''}/invite?token=${result.invite_token}`
    : '';

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-zinc-900">Invites</h1>
      <p className="text-zinc-500 text-sm mt-1">
        Invite new members to your organization
      </p>

      {/* Invite form */}
      <div className="mt-6 bg-white rounded-xl border border-zinc-200 shadow-sm p-6">
        <h2 className="text-sm font-semibold text-zinc-900 mb-4">Create invitation</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="invite_email"
              className="block text-sm font-medium text-zinc-700 mb-1.5"
            >
              Email address
            </label>
            <input
              id="invite_email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="invite@company.com"
              className="w-full px-3 py-2.5 rounded-lg border border-zinc-300 text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label
              htmlFor="invite_group"
              className="block text-sm font-medium text-zinc-700 mb-1.5"
            >
              Assign to group
            </label>
            {groupsLoading ? (
              <div className="h-10 bg-zinc-100 rounded-lg animate-pulse" />
            ) : (
              <select
                id="invite_group"
                required
                value={groupId}
                onChange={(e) => setGroupId(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg border border-zinc-300 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
              >
                <option value="">Select a group</option>
                {groups.map((g) => (
                  <option key={g.group_id} value={g.group_id}>
                    {g.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || groupsLoading}
            className="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-black font-medium rounded-lg px-5 py-2.5 text-sm transition-colors"
          >
            {loading ? 'Sending invite...' : 'Create invite'}
          </button>
        </form>
      </div>

      {/* Result */}
      {result && (
        <div className="mt-6 bg-white rounded-xl border border-zinc-200 shadow-sm p-6 space-y-5">
          <div>
            <p className="text-sm font-semibold text-zinc-900 mb-1">
              Invitation created for <span className="text-green-600">{result.email}</span>
            </p>
            <p className="text-xs text-zinc-400">
              Expires: {new Date(result.expires_at).toLocaleString()}
            </p>
          </div>

          {/* Token */}
          <div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
              Invite token
            </p>
            <div className="flex items-start gap-3">
              <code className="flex-1 bg-zinc-50 border border-zinc-200 rounded-lg px-4 py-3 text-sm font-mono text-zinc-800 break-all">
                {result.invite_token}
              </code>
              <button
                onClick={handleCopyToken}
                className="shrink-0 bg-green-500 hover:bg-green-600 text-black font-medium rounded-lg px-4 py-2.5 text-sm transition-colors"
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Invite link */}
          <div>
            <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-2">
              Invite link
            </p>
            <div className="flex items-start gap-3">
              <code className="flex-1 bg-zinc-50 border border-zinc-200 rounded-lg px-4 py-3 text-sm font-mono text-zinc-800 break-all">
                {inviteLink}
              </code>
              <button
                onClick={handleCopyLink}
                className="shrink-0 bg-green-500 hover:bg-green-600 text-black font-medium rounded-lg px-4 py-2.5 text-sm transition-colors"
              >
                Copy link
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
