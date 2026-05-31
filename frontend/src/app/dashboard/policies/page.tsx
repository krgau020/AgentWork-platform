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

  // Inline policy rename
  const [editingPolicyId, setEditingPolicyId] = useState<string | null>(null);
  const [editingPolicyName, setEditingPolicyName] = useState('');
  const [renameError, setRenameError] = useState('');
  const [renaming, setRenaming] = useState(false);

  // Inline statement edit
  const [editingStmt, setEditingStmt] = useState<{ policyId: string; statementId: string } | null>(null);
  const [editStmtResource, setEditStmtResource] = useState('');
  const [editStmtAction, setEditStmtAction] = useState('');
  const [editStmtEffect, setEditStmtEffect] = useState<'allow' | 'deny'>('allow');
  const [stmtEditError, setStmtEditError] = useState('');
  const [stmtSaving, setStmtSaving] = useState(false);

  // Add statement modal
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

  function startRename(policy: PolicyResponse) {
    setEditingPolicyId(policy.policy_id);
    setEditingPolicyName(policy.name);
    setRenameError('');
  }

  function cancelRename() {
    setEditingPolicyId(null);
    setEditingPolicyName('');
    setRenameError('');
  }

  async function handleRename(policyId: string) {
    const trimmed = editingPolicyName.trim();
    if (!trimmed) return;
    setRenameError('');
    setRenaming(true);
    try {
      const res = await api.updatePolicy(policyId, trimmed);
      if (!res.ok) {
        const d = await res.json();
        setRenameError(d.message || 'Something went wrong');
        return;
      }
      const updated: PolicyResponse = await res.json();
      setPolicies((prev) =>
        prev.map((p) => (p.policy_id === policyId ? { ...p, name: updated.name } : p))
      );
      setEditingPolicyId(null);
    } catch {
      setRenameError('Network error');
    } finally {
      setRenaming(false);
    }
  }

  function startEditStatement(policyId: string, stmt: StatementResponse) {
    setEditingStmt({ policyId, statementId: stmt.statement_id });
    setEditStmtResource(stmt.resource);
    setEditStmtAction(stmt.action);
    setEditStmtEffect(stmt.effect as 'allow' | 'deny');
    setStmtEditError('');
  }

  function cancelEditStatement() {
    setEditingStmt(null);
    setStmtEditError('');
  }

  async function handleSaveStatement() {
    if (!editingStmt) return;
    setStmtEditError('');
    setStmtSaving(true);
    try {
      const res = await api.updateStatement(
        editingStmt.policyId,
        editingStmt.statementId,
        editStmtResource,
        editStmtAction,
        editStmtEffect
      );
      if (!res.ok) {
        const d = await res.json();
        setStmtEditError(d.message || 'Something went wrong');
        return;
      }
      const updated: StatementResponse = await res.json();
      setPolicies((prev) =>
        prev.map((p) =>
          p.policy_id === editingStmt.policyId
            ? {
                ...p,
                statements: p.statements.map((s) =>
                  s.statement_id === editingStmt.statementId ? updated : s
                ),
              }
            : p
        )
      );
      setEditingStmt(null);
    } catch {
      setStmtEditError('Network error');
    } finally {
      setStmtSaving(false);
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
      const res = await api.addStatement(selectedPolicy.policy_id, stmtResource, stmtAction, stmtEffect);
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
          ? { ...p, statements: p.statements.filter((s) => s.statement_id !== statementId) }
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
              placeholder="e.g. member-read-platform"
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
            const isRenamingThis = editingPolicyId === policy.policy_id;

            return (
              <div
                key={policy.policy_id}
                className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
              >
                {/* Card header */}
                <div className="flex items-center justify-between px-6 py-4 gap-4">
                  {/* Policy name — normal or rename mode */}
                  {isRenamingThis ? (
                    <div className="flex items-center gap-2 flex-1">
                      <input
                        autoFocus
                        value={editingPolicyName}
                        onChange={(e) => setEditingPolicyName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleRename(policy.policy_id);
                          if (e.key === 'Escape') cancelRename();
                        }}
                        className="flex-1 px-2.5 py-1.5 rounded-lg border border-blue-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold"
                      />
                      <button
                        onClick={() => handleRename(policy.policy_id)}
                        disabled={renaming || !editingPolicyName.trim()}
                        className="text-xs bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg px-3 py-1.5 transition-colors"
                      >
                        {renaming ? 'Saving...' : 'Save'}
                      </button>
                      <button
                        onClick={cancelRename}
                        className="text-xs text-slate-500 hover:text-slate-700 font-medium px-2 py-1.5"
                      >
                        Cancel
                      </button>
                      {renameError && (
                        <span className="text-xs text-red-600">{renameError}</span>
                      )}
                    </div>
                  ) : (
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : policy.policy_id)}
                      className="flex items-center gap-3 text-left flex-1 min-w-0"
                    >
                      <span className="text-sm font-semibold text-slate-900 truncate">
                        {policy.name}
                      </span>
                      <span className="text-xs text-slate-400 shrink-0">
                        {policy.statements.length} statement
                        {policy.statements.length !== 1 ? 's' : ''}
                      </span>
                      <span className="text-slate-400 text-xs ml-auto shrink-0">
                        {isExpanded ? '▲' : '▼'}
                      </span>
                    </button>
                  )}

                  {/* Admin action buttons */}
                  {admin && !isRenamingThis && (
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => startRename(policy)}
                        className="text-xs text-slate-500 hover:text-slate-700 font-medium border border-slate-200 rounded-lg px-3 py-1.5 transition-colors"
                      >
                        Rename
                      </button>
                      <button
                        onClick={() => openAddStatement(policy)}
                        className="text-xs bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg px-3 py-1.5 transition-colors"
                      >
                        Add statement
                      </button>
                    </div>
                  )}
                </div>

                {/* Expanded statements */}
                {isExpanded && (
                  <div className="border-t border-slate-200">
                    {/* Statement edit error */}
                    {stmtEditError && editingStmt?.policyId === policy.policy_id && (
                      <div className="px-6 pt-3">
                        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
                          {stmtEditError}
                        </div>
                      </div>
                    )}

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
                                Actions
                              </th>
                            )}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {policy.statements.map((stmt) => {
                            const isEditingThis =
                              editingStmt?.policyId === policy.policy_id &&
                              editingStmt?.statementId === stmt.statement_id;

                            if (isEditingThis) {
                              return (
                                <tr key={stmt.statement_id} className="bg-blue-50">
                                  <td className="px-4 py-3">
                                    <input
                                      autoFocus
                                      value={editStmtResource}
                                      onChange={(e) => setEditStmtResource(e.target.value)}
                                      placeholder="platform:users"
                                      className="w-full px-2 py-1.5 rounded border border-blue-300 text-slate-900 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    />
                                  </td>
                                  <td className="px-4 py-3">
                                    <input
                                      value={editStmtAction}
                                      onChange={(e) => setEditStmtAction(e.target.value)}
                                      placeholder="read"
                                      className="w-full px-2 py-1.5 rounded border border-blue-300 text-slate-900 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    />
                                  </td>
                                  <td className="px-4 py-3">
                                    <select
                                      value={editStmtEffect}
                                      onChange={(e) =>
                                        setEditStmtEffect(e.target.value as 'allow' | 'deny')
                                      }
                                      className="px-2 py-1.5 rounded border border-blue-300 text-slate-900 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    >
                                      <option value="allow">Allow</option>
                                      <option value="deny">Deny</option>
                                    </select>
                                  </td>
                                  <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                      <button
                                        onClick={handleSaveStatement}
                                        disabled={stmtSaving}
                                        className="text-xs bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded px-2.5 py-1 transition-colors"
                                      >
                                        {stmtSaving ? 'Saving...' : 'Save'}
                                      </button>
                                      <button
                                        onClick={cancelEditStatement}
                                        className="text-xs text-slate-500 hover:text-slate-700 font-medium"
                                      >
                                        Cancel
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              );
                            }

                            return (
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
                                    <div className="flex items-center gap-3">
                                      <button
                                        onClick={() => startEditStatement(policy.policy_id, stmt)}
                                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                      >
                                        Edit
                                      </button>
                                      <button
                                        onClick={() =>
                                          handleRemoveStatement(policy.policy_id, stmt.statement_id)
                                        }
                                        className="text-red-500 hover:text-red-700 text-sm font-medium"
                                      >
                                        Remove
                                      </button>
                                    </div>
                                  </td>
                                )}
                              </tr>
                            );
                          })}
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
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Resource</label>
            <input
              type="text"
              required
              value={stmtResource}
              onChange={(e) => setStmtResource(e.target.value)}
              placeholder="e.g. platform:users"
              className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Action</label>
            <input
              type="text"
              required
              value={stmtAction}
              onChange={(e) => setStmtAction(e.target.value)}
              placeholder="e.g. read"
              className="w-full px-3 py-2.5 rounded-lg border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Effect</label>
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
