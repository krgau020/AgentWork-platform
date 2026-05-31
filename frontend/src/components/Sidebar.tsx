'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { getUser, getRefreshToken, clearTokens, isAdmin } from '@/lib/auth';
import { api, ServiceResponse } from '@/lib/api';

function NavItem({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
        active
          ? 'bg-green-500 text-black shadow-sm shadow-green-900/30'
          : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
      }`}
    >
      {children}
    </Link>
  );
}

function AgentWorkLogo() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="36" height="36" rx="10" fill="#22c55e" />
      <path
        d="M5,27 L11.5,8 L18,27 M8,18 L15,18 M18,8 L21,27 L25,15 L29,27 L32,8"
        stroke="#0a0a0a"
        strokeWidth="2.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function Sidebar() {
  const pathname     = usePathname();
  const router       = useRouter();
  const user         = getUser();
  const refreshToken = getRefreshToken();
  const [solutions, setSolutions] = useState<ServiceResponse[]>([]);

  useEffect(() => {
    api.listSolutions()
      .then(list => setSolutions(list.filter(s => s.is_active)))
      .catch(() => {});
  }, []);

  async function handleSignOut() {
    if (refreshToken) {
      try { await api.logout(refreshToken); } catch { /* ignore */ }
    }
    clearTokens();
    router.push('/login');
  }

  const onSolutions = pathname.startsWith('/dashboard/solutions');

  return (
    <div className="w-64 flex flex-col min-h-screen shrink-0" style={{ backgroundColor: '#0a0a0a' }}>

      {/* ── Brand ── */}
      <div className="px-5 py-6 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <AgentWorkLogo />
          <div>
            <span className="text-white font-bold text-xl tracking-tight leading-none">AgentWork</span>
            <p className="text-zinc-500 text-[11px] mt-0.5 leading-none">AI Platform</p>
          </div>
        </div>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 px-3 py-5 overflow-y-auto space-y-7">

        {/* SOLUTIONS — visible to all */}
        <div>
          <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-green-500">
            Solutions
          </p>

          <NavItem href="/dashboard" active={pathname === '/dashboard'}>
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Overview
          </NavItem>

          {solutions.length === 0 ? (
            <p className="px-3 py-2 text-xs text-zinc-600 italic">No solutions registered</p>
          ) : (
            solutions.map(s => (
              <NavItem key={s.service_id} href="/dashboard/solutions" active={onSolutions}>
                <span className="w-2 h-2 rounded-full bg-green-400 shrink-0" />
                <span className="truncate">{s.display_name || s.name}</span>
              </NavItem>
            ))
          )}
        </div>

        {/* ADMIN — only for admins */}
        {isAdmin() && (
          <div>
            <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-500">
              Admin
            </p>

            <NavItem href="/dashboard/users" active={pathname.startsWith('/dashboard/users')}>
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Users
            </NavItem>

            <NavItem href="/dashboard/groups" active={pathname.startsWith('/dashboard/groups')}>
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Groups
            </NavItem>

            <NavItem href="/dashboard/policies" active={pathname.startsWith('/dashboard/policies')}>
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Policies
            </NavItem>

            <NavItem href="/dashboard/invites" active={pathname.startsWith('/dashboard/invites')}>
              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Invites
            </NavItem>
          </div>
        )}
      </nav>

      {/* ── User + Sign out ── */}
      <div className="px-4 py-4 border-t border-zinc-800">
        {user && (
          <div className="mb-3 flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center shrink-0">
              <span className="text-black text-xs font-bold">
                {user.email[0].toUpperCase()}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-[11px] text-zinc-500 font-medium leading-none mb-0.5">Signed in as</p>
              <p className="text-sm text-zinc-300 truncate leading-tight" title={user.email}>
                {user.email}
              </p>
            </div>
          </div>
        )}
        <button
          onClick={handleSignOut}
          className="w-full text-left px-3 py-2 text-sm text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-xl transition-colors font-medium"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
