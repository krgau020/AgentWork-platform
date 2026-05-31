'use client';

import { useEffect, useState, FormEvent } from 'react';
import { api } from '@/lib/api';
import { isAdmin } from '@/lib/auth';
import Modal from '@/components/Modal';
import type { GroupResponse, PolicyResponse } from '@/lib/api';

export default function GroupsPage() {
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [newGroupName, setNewGroupName] = useState('');
  const [createError, setCreateError] = useState('');
  const [creating, setCreating] = useState(false);

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<GroupResponse | null>(null);
  const [policies, setPolicies] = useState<PolicyResponse[]>([]);
  const [selectedPolicyId, setSelectedPolicyId] = useState('');
  const [modalError, setModalError] = useState('');
  const [modalSuccess, setModalSuccess] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [assigning, setAssigning] = useState(false);

  const admin = isAdmin();

  useEffect(() => {
    loadGroups();
  }, [page]);

  async function loadGroups() {
    setLoading(true);
    setError('');
    try {
      const data = await api.listGroups(page, 10);
      setGroups(data.data);
      setTotalPages(data.pages);
    } catch {
      setError('Failed to load groups');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateGroup(e: FormEvent) {
    e.preventDefault();
    setCreateError('');
    setCreating(true);
    try {
      const res = await api.createGroup(newGroupName.trim());
      if (!res.ok) {
        const d = await res.json();
        setCreateError(d.message || 'Something went wrong');
        return;
      }
      setNewGroupName('');
      if (page === 1) {
        await loadGroups();
      } else {
        setPage(1);
      }
    } catch {
      setCreateError('Network error');
    } finally {
      setCreating(false);
    }
  }

  async function openAssignModal(group: GroupResponse) {
    setSelectedGroup(group);
    setModalError('');
    setModalSuccess('');
    setSelectedPolicyId('');
    setModalOpen(true);
    setModalLoading(true);
    try {
      const data = await api.listPolicies(1, 100);
      setPolicies(data.data);
    } catch {
      setModalError('Failed to load policies');
    } finally {
      setModalLoading(false);
    }
  }

  async function handleAssignPolicy() {
    if (!selectedGroup || !selectedPolicyId) return;
    setModalError('');
    setModalSuccess('');
    setAssigning(true);
    try {
      const res = await api.assignPolicyToGroup(selectedGroup.group_id, selectedPolicyId);
      if (!res.ok) {
        const d = await res.json();
        setModalError(d.message || 'Something went wrong');
        return;
      }
      setModalSuccess('Policy assigned successfully');
      setSelectedPolicyId('');
    } catch {
      setModalError('Network error');
    } finally {
      setAssigning(false);
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-zinc-900">Groups</h1>
      <p className="text-zinc-500 text-sm mt-1">Manage groups and their policy assignments</p>

      {/* Create group form — admin only */}
      {admin && (
        <form
          onSubmit={handleCreateGroup}
          className="mt-6 bg-white rounded-xl border border-zinc-200 shadow-sm p-6"
        >
          <h2 className="text-sm font-semibold text-zinc-900 mb-4">Create new group</h2>
          <div className="flex gap-3">
            <input
              type="text"
              required
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              placeholder="Group name"
              className="flex-1 px-3 py-2.5 rounded-lg border border-zinc-300 text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
            />
            <button
              type="submit"
              disabled={creating || !newGroupName.trim()}
              className="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-black font-medium rounded-lg px-5 py-2.5 text-sm transition-colors"
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

      {/* Table */}
      <div className="mt-6 bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-zinc-50 border-b border-zinc-200">
              <th className="text-xs font-semibold text-zinc-500 uppercase tracking-wide px-6 py-3 text-left">
                Group name
              </th>
              {admin && (
                <th className="text-xs font-semibold text-zinc-500 uppercase tracking-wide px-6 py-3 text-left">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {loading ? (
              <tr>
                <td colSpan={admin ? 2 : 1} className="px-6 py-8 text-center">
                  <div className="flex justify-center">
                    <div className="h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                </td>
              </tr>
            ) : groups.length === 0 ? (
              <tr>
                <td
                  colSpan={admin ? 2 : 1}
                  className="px-6 py-8 text-center text-sm text-zinc-500"
                >
                  No groups found
                </td>
              </tr>
            ) : (
              groups.map((group) => (
                <tr key={group.group_id} className="hover:bg-zinc-50">
                  <td className="px-6 py-4 text-sm text-zinc-900">{group.name}</td>
                  {admin && (
                    <td className="px-6 py-4 text-sm">
                      <button
                        onClick={() => openAssignModal(group)}
                        className="text-green-600 hover:text-green-800 font-medium text-sm"
                      >
                        Assign policy
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-black font-medium rounded-lg px-4 py-2 text-sm transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-zinc-500">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-black font-medium rounded-lg px-4 py-2 text-sm transition-colors"
          >
            Next
          </button>
        </div>
      )}

      {/* Assign Policy Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={`Assign policy — ${selectedGroup?.name ?? ''}`}
      >
        {modalLoading ? (
          <div className="flex justify-center py-8">
            <div className="h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="space-y-4">
            {modalError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
                {modalError}
              </div>
            )}
            {modalSuccess && (
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg px-4 py-2.5">
                {modalSuccess}
              </div>
            )}

            {policies.length === 0 ? (
              <p className="text-sm text-zinc-400">No policies available</p>
            ) : (
              <div className="space-y-3">
                <label className="block text-sm font-medium text-zinc-700">
                  Select a policy
                </label>
                <select
                  value={selectedPolicyId}
                  onChange={(e) => setSelectedPolicyId(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg border border-zinc-300 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                >
                  <option value="">Choose a policy</option>
                  {policies.map((p) => (
                    <option key={p.policy_id} value={p.policy_id}>
                      {p.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleAssignPolicy}
                  disabled={!selectedPolicyId || assigning}
                  className="w-full bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-black font-medium rounded-lg px-4 py-2.5 text-sm transition-colors"
                >
                  {assigning ? 'Assigning...' : 'Assign policy'}
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
