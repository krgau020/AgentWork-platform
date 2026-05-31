'use client';

import { useEffect, useRef, useState } from 'react';
import { api, ServiceResponse } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

export default function SolutionsPage() {
  const [solutions, setSolutions] = useState<ServiceResponse[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState('');

  const [selected, setSelected] = useState<ServiceResponse | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.listSolutions()
      .then(setSolutions)
      .catch(() => setListError('Failed to load solutions.'))
      .finally(() => setLoadingList(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  function selectSolution(s: ServiceResponse) {
    setSelected(s);
    setMessages([]);
    setChatError('');
    setInput('');
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || !selected || sending) return;

    setInput('');
    setChatError('');
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setSending(true);

    try {
      const res = await api.chatWithSolution(selected.name, text);
      const data = await res.json();
      if (!res.ok) {
        setChatError(data?.detail?.message || data?.message || 'Something went wrong.');
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', text: data.reply }]);
      }
    } catch {
      setChatError('Network error. Check that the solution is running.');
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex h-full min-h-[calc(100vh-0px)]">
      {/* ── Left panel: solution list ── */}
      <div className="w-72 shrink-0 border-r border-slate-200 bg-slate-50 flex flex-col">
        <div className="px-5 py-4 border-b border-slate-200">
          <h2 className="text-base font-semibold text-slate-800">Solutions</h2>
          <p className="text-xs text-slate-500 mt-0.5">Select a solution to start chatting</p>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
          {loadingList && (
            <p className="text-sm text-slate-500 px-2 py-4 text-center">Loading...</p>
          )}
          {!loadingList && listError && (
            <p className="text-sm text-red-500 px-2 py-4 text-center">{listError}</p>
          )}
          {!loadingList && !listError && solutions.length === 0 && (
            <p className="text-sm text-slate-500 px-2 py-4 text-center">
              No solutions registered yet.
            </p>
          )}
          {solutions.map((s) => {
            const active = selected?.service_id === s.service_id;
            return (
              <button
                key={s.service_id}
                onClick={() => selectSolution(s)}
                className={`w-full text-left rounded-xl px-4 py-3 transition-colors border ${
                  active
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-slate-200 hover:border-blue-300 hover:bg-blue-50 text-slate-800'
                }`}
              >
                <p className={`text-sm font-semibold ${active ? 'text-white' : 'text-slate-800'}`}>
                  {s.display_name || s.name}
                </p>
                <p className={`text-xs mt-0.5 ${active ? 'text-blue-100' : 'text-slate-500'}`}>
                  {s.name}
                </p>
                <span
                  className={`inline-block mt-2 text-xs px-2 py-0.5 rounded-full font-medium ${
                    active
                      ? 'bg-blue-500 text-white'
                      : s.is_active
                      ? 'bg-green-100 text-green-700'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {s.is_active ? 'Active' : 'Inactive'}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Right panel: chat ── */}
      <div className="flex-1 flex flex-col">
        {!selected ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-8">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p className="text-slate-600 font-medium">Pick a solution to start</p>
            <p className="text-sm text-slate-400 mt-1">
              Choose from the list on the left to open a chat session.
            </p>
          </div>
        ) : (
          <>
            {/* Chat header */}
            <div className="px-6 py-4 border-b border-slate-200 bg-white flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  {selected.display_name || selected.name}
                </p>
                <p className="text-xs text-slate-500">{selected.name}</p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4 bg-slate-50">
              {messages.length === 0 && !sending && (
                <div className="flex justify-center">
                  <p className="text-sm text-slate-400 bg-white border border-slate-200 rounded-xl px-4 py-2">
                    Send a message to get started
                  </p>
                </div>
              )}

              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[72%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-sm'
                        : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm shadow-sm'
                    }`}
                  >
                    {m.text}
                  </div>
                </div>
              ))}

              {sending && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                    <div className="flex gap-1 items-center h-4">
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}

              {chatError && (
                <div className="flex justify-center">
                  <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2">
                    {chatError}
                  </p>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input area */}
            <div className="px-6 py-4 border-t border-slate-200 bg-white">
              <div className="flex gap-3 items-end">
                <textarea
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
                  className="flex-1 resize-none rounded-xl border border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none px-4 py-3 text-sm text-slate-800 placeholder-slate-400 max-h-40 overflow-y-auto"
                  style={{ height: 'auto' }}
                  onInput={(e) => {
                    const el = e.currentTarget;
                    el.style.height = 'auto';
                    el.style.height = `${el.scrollHeight}px`;
                  }}
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || sending}
                  className="shrink-0 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-xl px-5 py-3 text-sm font-medium transition-colors"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
