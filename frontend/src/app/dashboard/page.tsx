'use client';

import { useEffect, useState } from 'react';
import { getUser } from '@/lib/auth';
import { api } from '@/lib/api';
import type { AuthUser } from '@/lib/auth';

interface Stats {
  users: number;
  groups: number;
  policies: number;
}

export default function DashboardPage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const currentUser = getUser();
    setUser(currentUser);

    async function loadStats() {
      try {
        const [usersData, groupsData, policiesData] = await Promise.all([
          api.listUsers(1, 1),
          api.listGroups(1, 1),
          api.listPolicies(1, 1),
        ]);
        setStats({
          users: usersData.total,
          groups: groupsData.total,
          policies: policiesData.total,
        });
      } catch {
        // Stats failed to load — leave null
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, []);

  const statCards = [
    { label: 'Total Users', value: stats?.users ?? '—' },
    { label: 'Total Groups', value: stats?.groups ?? '—' },
    { label: 'Total Policies', value: stats?.policies ?? '—' },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-slate-900">Overview</h1>
      <p className="text-slate-500 text-sm mt-1">Welcome back to your AgentWork dashboard</p>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-8">
        {statCards.map((card) => (
          <div
            key={card.label}
            className="bg-white rounded-xl border border-slate-200 shadow-sm p-6"
          >
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              {card.label}
            </p>
            {loading ? (
              <div className="h-8 w-12 mt-2 bg-slate-100 rounded animate-pulse" />
            ) : (
              <p className="text-3xl font-bold text-slate-900 mt-2">{card.value}</p>
            )}
          </div>
        ))}
      </div>

      {/* Session info */}
      <div className="mt-8 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Session information</h2>
        {user ? (
          <dl className="space-y-3">
            <div className="flex gap-4">
              <dt className="text-sm font-medium text-slate-500 w-24 shrink-0">Email</dt>
              <dd className="text-sm text-slate-900">{user.email}</dd>
            </div>
            <div className="flex gap-4">
              <dt className="text-sm font-medium text-slate-500 w-24 shrink-0">Org ID</dt>
              <dd className="text-sm text-slate-900 font-mono break-all">{user.org_id}</dd>
            </div>
            <div className="flex gap-4">
              <dt className="text-sm font-medium text-slate-500 w-24 shrink-0">Groups</dt>
              <dd className="text-sm text-slate-900">
                {user.groups.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {user.groups.map((g) => (
                      <span
                        key={g}
                        className="bg-slate-100 text-slate-700 text-xs font-medium px-2.5 py-0.5 rounded-full"
                      >
                        {g}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-slate-400">No groups</span>
                )}
              </dd>
            </div>
          </dl>
        ) : (
          <div className="h-4 bg-slate-100 rounded animate-pulse w-48" />
        )}
      </div>
    </div>
  );
}
