'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getUser } from '@/lib/auth';
import { api, ServiceResponse } from '@/lib/api';
import type { AuthUser } from '@/lib/auth';

interface Stats {
  users: number;
  groups: number;
  policies: number;
}

export default function DashboardPage() {
  const [user,      setUser]      = useState<AuthUser | null>(null);
  const [orgName,   setOrgName]   = useState<string | null>(null);
  const [stats,     setStats]     = useState<Stats | null>(null);
  const [solutions, setSolutions] = useState<ServiceResponse[]>([]);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    const currentUser = getUser();
    setUser(currentUser);

    async function load() {
      try {
        const requests: Promise<unknown>[] = [
          api.listUsers(1, 1),
          api.listGroups(1, 1),
          api.listPolicies(1, 1),
          api.listSolutions(),
        ];
        if (currentUser?.org_id) {
          requests.push(api.getOrg(currentUser.org_id));
        }
        const [usersData, groupsData, policiesData, solutionList, orgData] =
          await Promise.all(requests) as [
            Awaited<ReturnType<typeof api.listUsers>>,
            Awaited<ReturnType<typeof api.listGroups>>,
            Awaited<ReturnType<typeof api.listPolicies>>,
            Awaited<ReturnType<typeof api.listSolutions>>,
            Awaited<ReturnType<typeof api.getOrg>> | undefined,
          ];
        setStats({ users: usersData.total, groups: groupsData.total, policies: policiesData.total });
        setSolutions(solutionList.filter(s => s.is_active));
        if (orgData) setOrgName(orgData.name);
      } catch {
        // stats / solutions failed — leave null / empty
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <div className="p-8 space-y-10">

      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Overview</h1>
        <p className="text-zinc-500 text-sm mt-1">Welcome back to your AgentWork dashboard</p>
      </div>

      {/* ── Solutions launcher ── */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4">
          Your Solutions
        </h2>

        {loading && (
          <div className="flex gap-4">
            {[1, 2].map(i => (
              <div key={i} className="w-48 h-28 bg-zinc-100 rounded-2xl animate-pulse" />
            ))}
          </div>
        )}

        {!loading && solutions.length === 0 && (
          <div className="bg-zinc-50 border border-zinc-200 rounded-xl px-6 py-8 text-center max-w-sm">
            <p className="text-sm text-zinc-500 font-medium">No solutions available yet</p>
            <p className="text-xs text-zinc-400 mt-1">
              Ask an admin to register a solution in the platform.
            </p>
          </div>
        )}

        {!loading && solutions.length > 0 && (
          <div className="flex flex-wrap gap-4">
            {solutions.map(s => (
              <SolutionCard key={s.service_id} solution={s} />
            ))}
          </div>
        )}
      </section>

      {/* ── Platform stats ── */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4">
          Platform
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {[
            { label: 'Total Users',    value: stats?.users },
            { label: 'Total Groups',   value: stats?.groups },
            { label: 'Total Policies', value: stats?.policies },
          ].map(card => (
            <div key={card.label} className="bg-white rounded-xl border border-zinc-200 shadow-sm p-6">
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wide">
                {card.label}
              </p>
              {loading ? (
                <div className="h-8 w-12 mt-2 bg-zinc-100 rounded animate-pulse" />
              ) : (
                <p className="text-3xl font-bold text-zinc-900 mt-2">{card.value ?? '—'}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Session info ── */}
      <section>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4">
          Session
        </h2>
        <div className="bg-white rounded-xl border border-zinc-200 shadow-sm p-6">
          {user ? (
            <dl className="space-y-3">
              <Row label="Email"        value={user.email} />
              <Row label="Organization" value={orgName ?? <span className="text-zinc-400">—</span>} />
              <Row label="Groups" value={
                user.groups.length > 0
                  ? <div className="flex flex-wrap gap-2">
                      {user.groups.map(g => (
                        <span key={g} className="bg-green-100 text-green-700 text-xs font-medium px-2.5 py-0.5 rounded-full">
                          {g}
                        </span>
                      ))}
                    </div>
                  : <span className="text-zinc-400">No groups</span>
              } />
            </dl>
          ) : (
            <div className="h-4 bg-zinc-100 rounded animate-pulse w-48" />
          )}
        </div>
      </section>
    </div>
  );
}

function SolutionCard({ solution: s }: { solution: ServiceResponse }) {
  return (
    <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 w-52 flex flex-col gap-3 hover:border-green-400 hover:shadow-md transition-all">
      <div className="w-9 h-9 rounded-xl bg-green-100 flex items-center justify-center">
        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </div>
      <div>
        <p className="text-sm font-semibold text-zinc-800 leading-tight">{s.display_name || s.name}</p>
        <p className="text-xs text-zinc-500 mt-0.5 font-mono">{s.name}</p>
      </div>
      <Link
        href="/dashboard/solutions"
        className="mt-auto text-xs font-semibold text-green-600 hover:text-green-700 flex items-center gap-1"
      >
        Launch
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-4">
      <dt className="text-sm font-medium text-zinc-500 w-20 shrink-0">{label}</dt>
      <dd className="text-sm text-zinc-900">{value}</dd>
    </div>
  );
}
