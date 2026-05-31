'use client';

import { useEffect, useState } from 'react';
import { api, ServiceResponse } from '@/lib/api';

export default function SolutionsPage() {
  const [solutions, setSolutions] = useState<ServiceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.listSolutions()
      .then(setSolutions)
      .catch(() => setError('Failed to load solutions.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">Solutions</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Registered AI solutions available on this platform. Click <strong>Open</strong> to launch a solution in its own interface.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-500 text-sm">
          <div className="h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Loading solutions...
        </div>
      )}

      {!loading && error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-4 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && solutions.length === 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl px-6 py-10 text-center">
          <p className="text-slate-500 font-medium">No solutions registered yet.</p>
          <p className="text-slate-400 text-sm mt-1">
            An admin can register a solution via <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">POST /api/v1/registry/register</code>.
          </p>
        </div>
      )}

      {!loading && !error && solutions.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {solutions.map((s) => (
            <SolutionCard key={s.service_id} solution={s} />
          ))}
        </div>
      )}
    </div>
  );
}

function SolutionCard({ solution: s }: { solution: ServiceResponse }) {
  const accessLabel =
    s.allowed_groups.includes('*')
      ? 'Everyone'
      : s.allowed_groups.join(', ');

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <span
          className={`text-xs font-medium px-2.5 py-1 rounded-full ${
            s.is_active
              ? 'bg-green-100 text-green-700'
              : 'bg-slate-100 text-slate-500'
          }`}
        >
          {s.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      {/* Info */}
      <div>
        <p className="text-base font-semibold text-slate-800">{s.display_name || s.name}</p>
        <p className="text-xs text-slate-500 mt-0.5 font-mono">{s.name}</p>
      </div>

      {/* Meta */}
      <div className="space-y-1.5 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Access</span>
          <span className="font-medium text-slate-700">{accessLabel}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Health</span>
          <span className="font-mono text-slate-600">{s.health_endpoint}</span>
        </div>
        {s.registered_at && (
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Registered</span>
            <span className="text-slate-600">
              {new Date(s.registered_at).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      {/* Open button */}
      <a
        href="http://localhost:8004"
        target="_blank"
        rel="noopener noreferrer"
        className={`mt-auto w-full text-center py-2.5 rounded-xl text-sm font-medium transition-colors ${
          s.is_active
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-slate-100 text-slate-400 cursor-not-allowed pointer-events-none'
        }`}
      >
        Open Solution
      </a>
    </div>
  );
}
