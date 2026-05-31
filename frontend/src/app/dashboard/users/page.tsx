'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { isAdmin } from '@/lib/auth';
import Modal from '@/components/Modal';
import type { UserResponse, GroupResponse } from '@/lib/api';

export default function UsersPage() {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null);
  const [userGroups, setUserGroups] = useState<GroupResponse[]>([]);
  const [allGroups, setAllGroups] = useState<GroupResponse[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState('');
  const [modalError, setModalError] = useState('');
  const [modalLoading, setModalLoading] = useState(false);

  const admin = isAdmin();

  useEffect(() => {
    loadUsers();
  }, [page]);

  async function loadUsers() {
    setLoading(true);
    setError('');
    try {
      const data = await api.listUsers(page, 10);
      setUsers(data.data);
      setTotalPages(data.pages);
    } catch {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  }

  async function openGroupsModal(user: UserResponse) {
    setSelectedUser(user);
    setModalError('');
    setSelectedGroupId('');
    setModalOpen(true);
    setModalLoading(true);
    try {
      const [groups, all] = await Promise.all([
        api.getUserGroups(user.user_id),
        api.listGroups(1, 100),
      ]);
      setUserGroups(groups);
      setAllGroups(all.data);
    } catch {
      setModalError('Failed to load groups');
    } finally {
      setModalLoading(false);
    }
  }

  async function handleAddGroup() {
    if (!selectedUser || !selectedGroupId) return;
    setModalError('');
    const res = await api.addUserToGroup(selectedUser.user_id, selectedGroupId);
    if (!res.ok) {
      const d = await res.json();
      setModalError(d.message || 'Something went wrong');
      return;
    }
    const updated = await api.getUserGroups(selectedUser.user_id);
    setUserGroups(updated);
    setSelectedGroupId('');
  }

  async function handleRemoveGroup(groupId: string) {
    if (!selectedUser) return;
    setModalError('');
    const res = await api.removeUserFromGroup(selectedUser.user_id, groupId);
    if (!res.ok) {
      const d = await res.json();
      setModalError(d.message || 'Something went wrong');
      return;
    }
    const updated = await api.getUserGroups(selectedUser.user_id);
    setUserGroups(updated);
  }

  const availableGroups = allGroups.filter(
    (g) => !userGroups.some((ug) => ug.group_id === g.group_id)
  );

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-zinc-900">Users</h1>
      <p className="text-zinc-500 text-sm mt-1">Manage users in your organization</p>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
          {error}
        </div>
      )}

      <div className="mt-6 bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-zinc-50 border-b border-zinc-200">
              <th className="text-xs font-semibold text-zinc-500 uppercase tracking-wide px-6 py-3 text-left">
                Email
              </th>
              <th className="text-xs font-semibold text-zinc-500 uppercase tracking-wide px-6 py-3 text-left">
                Status
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
                <td colSpan={admin ? 3 : 2} className="px-6 py-8 text-center">
                  <div className="flex justify-center">
                    <div className="h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td
                  colSpan={admin ? 3 : 2}
                  className="px-6 py-8 text-center text-sm text-zinc-500"
                >
                  No users found
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.user_id} className="hover:bg-zinc-50">
                  <td className="px-6 py-4 text-sm text-zinc-900">{user.email}</td>
                  <td className="px-6 py-4 text-sm">
                    {user.is_active ? (
                      <span className="bg-green-50 text-green-700 text-xs font-medium px-2.5 py-0.5 rounded-full">
                        Active
                      </span>
                    ) : (
                      <span className="bg-zinc-100 text-zinc-500 text-xs font-medium px-2.5 py-0.5 rounded-full">
                        Inactive
                      </span>
                    )}
                  </td>
                  {admin && (
                    <td className="px-6 py-4 text-sm">
                      <button
                        onClick={() => openGroupsModal(user)}
                        className="text-green-600 hover:text-green-800 font-medium text-sm"
                      >
                        Manage groups
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

      {/* Groups Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={`Manage groups — ${selectedUser?.email ?? ''}`}
      >
        {modalLoading ? (
          <div className="flex justify-center py-8">
            <div className="h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="space-y-6">
            {modalError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5">
                {modalError}
              </div>
            )}

            {/* Current groups */}
            <div>
              <h3 className="text-sm font-semibold text-zinc-700 mb-3">Current groups</h3>
              {userGroups.length === 0 ? (
                <p className="text-sm text-zinc-400">Not in any groups</p>
              ) : (
                <ul className="space-y-2">
                  {userGroups.map((g) => (
                    <li
                      key={g.group_id}
                      className="flex items-center justify-between py-2 px-3 bg-zinc-50 rounded-lg"
                    >
                      <span className="text-sm text-zinc-900">{g.name}</span>
                      <button
                        onClick={() => handleRemoveGroup(g.group_id)}
                        className="text-red-500 hover:text-red-700 text-sm font-medium"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Add to group */}
            {availableGroups.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-zinc-700 mb-3">Add to group</h3>
                <div className="flex gap-2">
                  <select
                    value={selectedGroupId}
                    onChange={(e) => setSelectedGroupId(e.target.value)}
                    className="flex-1 px-3 py-2.5 rounded-lg border border-zinc-300 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                  >
                    <option value="">Select a group</option>
                    {availableGroups.map((g) => (
                      <option key={g.group_id} value={g.group_id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleAddGroup}
                    disabled={!selectedGroupId}
                    className="bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-black font-medium rounded-lg px-4 py-2 text-sm transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
