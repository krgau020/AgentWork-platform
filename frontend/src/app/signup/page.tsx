'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

function AgentWorkLogo() {
  return (
    <svg width="48" height="48" viewBox="0 0 36 36" fill="none">
      <rect width="36" height="36" rx="10" fill="#22c55e" />
      <path d="M5,27 L11.5,8 L18,27 M8,18 L15,18 M18,8 L21,27 L25,15 L29,27 L32,8" stroke="#0a0a0a" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function SignupPage() {
  const router = useRouter();
  const [orgName,  setOrgName]  = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.signup(email, password, orgName);
      if (!res.ok) {
        const d = await res.json();
        setError(d.message || 'Something went wrong');
        return;
      }
      router.push('/login');
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Left panel — brand ── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12" style={{ backgroundColor: '#0a0a0a' }}>
        <div className="flex items-center gap-3">
          <AgentWorkLogo />
          <span className="text-white text-2xl font-bold tracking-tight">AgentWork</span>
        </div>

        <div>
          <h1 className="text-5xl font-bold text-white leading-tight">
            Start building<br />
            <span className="text-green-400">in minutes.</span>
          </h1>
          <p className="text-zinc-400 mt-6 text-lg leading-relaxed max-w-sm">
            Create your organization, invite your team, and connect AI solutions — all from one platform.
          </p>

          <div className="mt-12 grid grid-cols-2 gap-4">
            {[
              { value: '10',   label: 'DB tables ready' },
              { value: '∞',    label: 'Solutions' },
              { value: 'PBAC', label: 'Access model' },
              { value: '2h',   label: 'Token lifetime' },
            ].map(s => (
              <div key={s.label} className="bg-zinc-900 rounded-2xl p-4 border border-zinc-800">
                <p className="text-green-400 text-2xl font-bold">{s.value}</p>
                <p className="text-zinc-500 text-xs mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-zinc-700 text-xs">© 2026 AgentWork Platform</p>
      </div>

      {/* ── Right panel — form ── */}
      <div className="flex-1 flex items-center justify-center px-8 bg-green-100">
        <div className="w-full max-w-sm">

          {/* Mobile brand */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <AgentWorkLogo />
            <span className="text-zinc-900 text-xl font-bold">AgentWork</span>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-zinc-900">Create your org</h2>
            <p className="text-zinc-500 mt-1.5 text-base">Set up your organization and admin account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="org_name" className="block text-sm font-semibold text-zinc-700 mb-1.5">
                Organization name
              </label>
              <input
                id="org_name" type="text" required
                value={orgName} onChange={e => setOrgName(e.target.value)}
                placeholder="Acme Corp"
                className="w-full px-4 py-3 rounded-xl border border-zinc-300 bg-white text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm transition-shadow"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-zinc-700 mb-1.5">
                Email address
              </label>
              <input
                id="email" type="email" required
                value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-4 py-3 rounded-xl border border-zinc-300 bg-white text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm transition-shadow"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-zinc-700 mb-1.5">
                Password
              </label>
              <input
                id="password" type="password" required
                value={password} onChange={e => setPassword(e.target.value)}
                placeholder="Create a strong password"
                className="w-full px-4 py-3 rounded-xl border border-zinc-300 bg-white text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm transition-shadow"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
                {error}
              </div>
            )}

            <button
              type="submit" disabled={loading}
              className="w-full bg-green-1000 hover:bg-green-600 disabled:bg-green-300 text-black font-semibold rounded-xl px-4 py-3 text-sm transition-colors shadow-sm"
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-zinc-500 mt-6">
            Already have an account?{' '}
            <Link href="/login" className="text-green-600 hover:text-green-700 font-semibold">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
