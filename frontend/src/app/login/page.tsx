'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { setTokens, isAuthenticated } from '@/lib/auth';

function AgentWorkLogo() {
  return (
    <svg width="48" height="48" viewBox="0 0 36 36" fill="none">
      <rect width="36" height="36" rx="10" fill="#22c55e" />
      <path d="M5,27 L11.5,8 L18,27 M8,18 L15,18 M18,8 L21,27 L25,15 L29,27 L32,8" stroke="#0a0a0a" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  useEffect(() => {
    if (isAuthenticated()) router.push('/dashboard');
  }, [router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.login(email, password);
      if (!res.ok) {
        const d = await res.json();
        setError(d.message || 'Something went wrong');
        return;
      }
      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      router.push('/dashboard');
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
            Your AI platform,<br />
            <span className="text-green-400">ready to scale.</span>
          </h1>
          <p className="text-zinc-400 mt-6 text-lg leading-relaxed max-w-sm">
            Auth, access control, and intelligent routing — all in one platform. Plug in any AI solution in minutes.
          </p>

          <div className="mt-12 flex flex-col gap-4">
            {[
              { label: 'Multi-tenant by default', desc: 'Every org is fully isolated' },
              { label: 'Policy-based access control', desc: 'Fine-grained permissions per group' },
              { label: 'Plug-and-play solutions',  desc: 'Register any AI service in one API call' },
            ].map(f => (
              <div key={f.label} className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-green-1000 flex items-center justify-center shrink-0 mt-0.5">
                  <svg className="w-3 h-3" fill="none" stroke="#0a0a0a" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-white text-sm font-semibold">{f.label}</p>
                  <p className="text-zinc-500 text-xs mt-0.5">{f.desc}</p>
                </div>
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
            <h2 className="text-3xl font-bold text-zinc-900">Welcome back</h2>
            <p className="text-zinc-500 mt-1.5 text-base">Sign in to your account to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
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
                placeholder="Enter your password"
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
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="text-center text-sm text-zinc-500 mt-6">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="text-green-600 hover:text-green-700 font-semibold">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
