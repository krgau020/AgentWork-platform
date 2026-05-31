'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { getUser, getRefreshToken, clearTokens } from '@/lib/auth';
import { api } from '@/lib/api';

const navItems = [
  { label: 'Overview', href: '/dashboard' },
  { label: 'Solutions', href: '/dashboard/solutions' },
  { label: 'Users', href: '/dashboard/users' },
  { label: 'Groups', href: '/dashboard/groups' },
  { label: 'Policies', href: '/dashboard/policies' },
  { label: 'Invites', href: '/dashboard/invites' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();
  const refreshToken = getRefreshToken();

  function isActive(href: string): boolean {
    if (href === '/dashboard') {
      return pathname === '/dashboard';
    }
    return pathname.startsWith(href);
  }

  async function handleSignOut() {
    if (refreshToken) {
      try {
        await api.logout(refreshToken);
      } catch {
        // Ignore logout errors — clear tokens regardless
      }
    }
    clearTokens();
    router.push('/login');
  }

  return (
    <div className="w-64 bg-slate-900 flex flex-col min-h-screen shrink-0">
      {/* Logo / Brand */}
      <div className="px-6 py-5 border-b border-slate-800">
        <span className="text-white font-bold text-lg tracking-tight">AgentWork</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom user section */}
      <div className="px-4 py-4 border-t border-slate-800">
        {user && (
          <div className="mb-3">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">
              Signed in as
            </p>
            <p className="text-sm text-slate-300 truncate" title={user.email}>
              {user.email}
            </p>
          </div>
        )}
        <button
          onClick={handleSignOut}
          className="w-full text-left px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors font-medium"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
