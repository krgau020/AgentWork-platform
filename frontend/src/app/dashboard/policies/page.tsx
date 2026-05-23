'use client';

import { useEffect, useState, FormEvent } from 'react';
import { api } from '@/lib/api';
import { isAdmin } from '@/lib/auth';
import Modal from '@/components/Modal';
import type { PolicyResponse, StatementResponse } from '@/lib/api';

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<PolicyResponse[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [newPolicyName, setNewPolicyName] = useState('');
  const [createError, setCreateError] = useState('');
  const [creating, setCreating] = useState(false);

  const [expandedId, setExpandedId] = useState<string | null>(null);

  const [statementModalOpen, setStatementModalOpen] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyResponse | null>(null);
  const [stmtResource, setStmtResource] = useState('');
  const [stmtAction, setStmtAction] = useState('');
  const [stmtEffect, setStmtEffect] = useState<'allow' | 'deny'>('allow');
  const [stmtError, setStmtError] = useState('');
  const [stmtAdding, setStmtAdding] = useState(false);

  const admin = isAdmin();

  useEffect(() => {
    loadPolicies();
  }, [page]);

  async function loadPolicies() {
    setLoading(true);
    setError('');
    try {
      const data = await api.listPolicies(page, 10);
      setPolicies(data.data);
      setTotalPages(data.pages);
    } catch {
      setError('Failed to load policies');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreatePolicy(e: FormEvent) {
    e.preventDefault();
    setCreateError('');
    setCreating(true);
    try {
      const res = await api.createPolicy(newPolicyName.trim());
      if (!res.ok) {
        const d = await res.json();
        setCreateError(d.message || 'Something went wrong');
        return;
      }
      setNewPolicyName('');
      if (page === 1) {
        await loadPolicies();
      } else {
        setPage(1);
      }
    } catch {
      setCreateError('Network error');
    } finally {
      setCreating(false);
    }
  }

  function openAddStatement(policy: PolicyResponse) {
    setSelectedPolicy(policy);
    setStmtResource('');
    setStmtAction('');
    setStmtEffect('allow');
    setStmtError('');
    setStatementModalOpen(true);
  }

  async function handleAddStatement(e: FormEvent) {
    e.preventDefault();
    if (!selectedPolicy) return;
    setStmtError('');
    setStmtAdding(true);
    try {
      const res = await api.addStatement(
        selectedPolicy.policy_id,
        stmtResource,
        stmtAction,
        stmtEffect
      );
      if (!res.ok) {
        const d = await res.json();
        setStmtError(d.message || 'Something went wrong');
        return;
      }
      const newStatement: StatementResponse = await res.json();
      setPolicies((prev) =>
        prev.map((p) =>
          p.policy_id === selectedPolicy.policy_id
            ? { ...p, statements: [...p.statements, newStatement] }
            : p
        )
      );
      setStatementModalOpen(false);
    } catch {
      setStmtError('Network error');
    } finally {
      setStmtAdding(false);
    }
  }

  async function handleRemoveStatement(policyId: string, statementId: string) {
    const res = await api.removeStatement(policyId, statementId);
    if (!res.ok) return;
    setPolicies((prev) =>
      prev.map((p) =>
        p.policy_id === policyId
          ? {
              ...p,
              statements: p.statements.filter((s) => s.statement_id !== statementId),
            }
          : p
      )
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-slate-900">Policies</h1>
      <p className="text-slate-500 text-sm mt-1">
        Manage access control policies and their statements
      </p>

      {/* Create policy form — admin only */}
      {admin && (
        <form
          onSubmit={handleCreatePolicy}
          className="mt-6 bg-white rounded-xl border border-slate-200 shadow-sm p-6"
        >
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Create new policy</h2>
          <div className="flex gap-3">
            <input
              type="text"
              required
              value={newPolicyName}
              onChange={(e) => setNewPolicyName(e.target.value)}
              placeholder="Policy name"
              className="flex-1 px-3 py-2.5 rounded-lg border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
            <button
              type="submit"
              disabled={creating || !newPolicyName.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg px-5 py-2.5 text-sm transition-colors"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
          {createError && (
            <div className="mt-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
              {createError}
            </div>
          )}
        </form>
      )}

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
          {error}
        </div>
      )}

      {/* Policy cards */}
      <div className="mt-6 space-y-3">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : policies.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm px-6 py-8 text-center text-sm text-slate-500">
            No policies found
          </div>
        ) : (
          policies.map((policy) => {
            const isExpanded = expandedId === policy.policy_id;
            return (
              <div
                key={policy.policy_id}
                className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
              >
                {/* Card header */}
                <div className="flex items-center justify-between px-6 py-4">
                  <button
                    onClick={() =>
                      setExpandedId(isExpanded ? null : policy.policy_id)
                    }
                    className="flex items-center gap-3 text-left flex-1"
                  >
                    <span className="text-sm font-semibold text-slate-900">
                      {policy.name}
                    </span>
                    <span className="text-xs text-slate-400">
                      {policy.statements.length} statement
                      {policy.statements.length !== 1 ? 's' : ''}
                    </span>
                    <span className="text-slate-400 text-xs ml-auto">
                      {isExpanded ? '▲' : '▼'}
                    </span>
                  </button>

                  {admin && (
                    <button
                      onClick={() => openAddStatement(policy)}
                      className="ml-4 text-sm bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg px-3 py-1.5 transition-colors shrink-0"
                    >
                      Add statement
                    </button>
                  )}
                </div>

                {/* Expanded statements */}
                {isExpanded && (
                  <div className="border-t border-slate-200">
                    {policy.statements.length === 0 ? (
                      <p className="px-6 py-4 text-sm text-slate-400">No statements</p>
                    ) : (
                      <table className="w-full">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200">
                            <th className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-6 py-3 text-left">
                              Resource
                            </th>
                            <th className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-6 py-3 text-left">
                              Action
                            </th>
                            <th className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-6 py-3 text-left">
                              Effect
                            </th>
                            {admin && (
                              <th className="text-xs font-semibold text-slate-500 uppercase tracking-wide px-6 py-3 text-left">
                                Remove
                              </th>
                            )}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {policy.statements.map((stmt) => (
                            <tr key={stmt.statement_id} className="hover:bg-slate-50">
                              <td className="px-6 py-4 text-sm text-slate-900 font-mono">
                                {stmt.resource}
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-900 font-mono">
                                {stmt.action}
                              </td>
                              <td className="px-6 py-4 text-sm">
                                {stmt.effect === 'allow' ? (
                                  <span className="bg-green-50 text-green-700 text-xs font-medium px-2.5 py-0.5 rounded-full">
                                    Allow
                                  </span>
                                ) : (
                                  <span className="bg-red-50 text-red-700 text-xs font-medium px-2.5 py-0.5 rounded-full">
                                    Deny
                                  </span>
                                )}
                              </td>
                              {admin && (
                                <td className="px-6 py-4 text-sm">
                                  <button
                                    onClick={() =>
                                      handleRemoveStatement(
                                        policy.policy_id,
                                        stmt.statement_id
                                      )
                                    }
                                    className="text-red-500 hover:text-red-700 text-sm font-medium"
                                  >
                                    Remove
                                  </button>
                                </td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg px-4 py-2 text-sm transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-slate-500">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg px-4 py-2 text-sm transition-colors"
          >
            Next
          </button>
        </div>
      )}

      {/* Add Statement Modal */}
      <Modal
        open={statementModalOpen}
        onClose={() => setStatementModalOpen(false)}
        title={`Add statement — ${selectedPolicy?.name ?? ''}`}
      >
        <form onSubmit={handleAddStatement} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Resource
            </label>
            <input
              type="text"
              required
              value={stmtResource}
              onChange={(e) => setStmtResource(e.target.value)}
              placeholder="e.g. arn:aws:s3:::my-bucket/*"
              className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Action
            </label>
            <input
              type="text"
              required
              value={stmtAction}
              onChange={(e) => setStmtAction(e.target.value)}
              placeholder="e.g. s3:GetObject"
              className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Effect
            </label>
            <select
              value={stmtEffect}
              onChange={(e) => setStmtEffect(e.target.value as 'allow' | 'deny')}
              className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              <option value="allow">Allow</option>
              <option value="deny">Deny</option>
            </select>
          </div>

          {stmtError && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
              {stmtError}
            </div>
          )}

          <button
            type="submit"
            disabled={stmtAdding}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg px-4 py-2.5 text-sm transition-colors"
          >
            {stmtAdding ? 'Adding...' : 'Add statement'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
