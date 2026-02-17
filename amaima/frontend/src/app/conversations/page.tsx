'use client';

import { useState, useEffect, useCallback } from 'react';
import { MessageSquare, Plus, Send, Loader2, Clock, Cpu, AlertCircle, Key, User, Bot } from 'lucide-react';

interface Message {
  role: string;
  content: string;
  model_used?: string;
  latency_ms?: number;
  timestamp?: string;
}

interface Conversation {
  id: string;
  title: string;
  operation_type?: string;
  created_at: string;
  updated_at?: string;
  messages: Message[];
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [needsAuth, setNeedsAuth] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/conversations');
      if (res.status === 401 || res.status === 403) {
        setNeedsAuth(true);
        setLoading(false);
        return;
      }
      if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
      const data = await res.json();
      const convs = data.conversations || data || [];
      setConversations(convs);
      if (convs.length > 0 && !selected) {
        setSelected(convs[0]);
      }
    } catch (err: any) {
      setNeedsAuth(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleSend = async () => {
    if (!input.trim() || !selected) return;
    setSending(true);
    try {
      const res = await fetch(`/api/v1/conversations/${selected.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: input, role: 'user' }),
      });
      if (res.ok) {
        setInput('');
        fetchConversations();
      }
    } catch (err) {
      setError('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      const res = await fetch('/api/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' }),
      });
      if (res.ok) {
        fetchConversations();
      }
    } catch (err) {
      setError('Failed to create conversation');
    }
  };

  if (needsAuth) {
    return (
      <div className="min-h-screen bg-gray-950 pt-14">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <MessageSquare className="w-7 h-7 text-cyan-400" />
            Conversations
          </h1>

          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-8 text-center">
            <Key className="w-12 h-12 text-cyan-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Connect your API Key</h2>
            <p className="text-gray-400 mb-6 max-w-md mx-auto">
              Conversations require authentication. Generate an API key from the Billing page and configure it to start using conversations.
            </p>
            <a
              href="/billing"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm font-medium text-white transition-colors"
            >
              <Key className="w-4 h-4" />
              Go to Billing
            </a>
          </div>

          <div className="mt-8 flex gap-6 opacity-50 pointer-events-none">
            <div className="w-80 flex-shrink-0 space-y-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Conversations</h3>
                <button className="p-2 rounded-lg bg-gray-800 text-gray-400">
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-3 rounded-lg bg-gray-900 border border-gray-800">
                  <div className="h-4 w-3/4 bg-gray-800 rounded mb-2" />
                  <div className="h-3 w-1/2 bg-gray-800/50 rounded" />
                </div>
              ))}
            </div>

            <div className="flex-1 bg-gray-900/60 border border-gray-800 rounded-xl flex flex-col">
              <div className="p-4 border-b border-gray-800">
                <div className="h-5 w-48 bg-gray-800 rounded" />
              </div>
              <div className="flex-1 p-6 space-y-4">
                {[1, 2].map((i) => (
                  <div key={i} className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
                    <div className={`max-w-md p-4 rounded-xl ${i % 2 === 0 ? 'bg-gray-800' : 'bg-cyan-900/30'}`}>
                      <div className="h-4 w-64 bg-gray-700 rounded mb-2" />
                      <div className="h-3 w-32 bg-gray-700/50 rounded" />
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 border-t border-gray-800">
                <div className="flex gap-3">
                  <div className="flex-1 h-10 bg-gray-800 rounded-lg" />
                  <div className="w-10 h-10 bg-gray-800 rounded-lg" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 pt-14">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
          <MessageSquare className="w-7 h-7 text-cyan-400" />
          Conversations
        </h1>

        {error && (
          <div className="mb-4 bg-red-900/30 border border-red-600 rounded-lg p-3 flex items-center gap-2 text-red-300 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200 text-xs">Dismiss</button>
          </div>
        )}

        <div className="flex gap-6 h-[calc(100vh-12rem)]">
          <div className="w-80 flex-shrink-0 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Conversations</h3>
              <button
                onClick={handleNewConversation}
                className="p-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition-colors"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2">
              {loading ? (
                <div className="text-center py-8 text-gray-400">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                  Loading...
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No conversations yet</p>
                </div>
              ) : (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => setSelected(conv)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selected?.id === conv.id
                        ? 'border-cyan-500/50 bg-cyan-900/20'
                        : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                    }`}
                  >
                    <p className="text-sm text-white font-medium truncate">{conv.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {conv.operation_type && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-purple-900/40 text-purple-300">
                          {conv.operation_type}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(conv.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="flex-1 bg-gray-900/60 border border-gray-800 rounded-xl flex flex-col">
            {selected ? (
              <>
                <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">{selected.title}</h2>
                    <div className="flex items-center gap-3 mt-1">
                      {selected.operation_type && (
                        <span className="text-xs px-2 py-0.5 rounded bg-purple-900/40 text-purple-300">
                          {selected.operation_type}
                        </span>
                      )}
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(selected.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {(!selected.messages || selected.messages.length === 0) ? (
                    <div className="text-center py-12 text-gray-500">
                      <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-40" />
                      <p>No messages yet. Start the conversation below.</p>
                    </div>
                  ) : (
                    selected.messages.map((msg, idx) => (
                      <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-lg rounded-xl p-4 ${
                          msg.role === 'user'
                            ? 'bg-cyan-900/30 border border-cyan-700/30'
                            : 'bg-gray-800 border border-gray-700'
                        }`}>
                          <div className="flex items-center gap-2 mb-2">
                            {msg.role === 'user' ? (
                              <User className="w-4 h-4 text-cyan-400" />
                            ) : (
                              <Bot className="w-4 h-4 text-purple-400" />
                            )}
                            <span className="text-xs font-medium text-gray-400 capitalize">{msg.role}</span>
                          </div>
                          <p className="text-sm text-gray-200 whitespace-pre-wrap">{msg.content}</p>
                          {(msg.model_used || msg.latency_ms) && (
                            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                              {msg.model_used && (
                                <span className="flex items-center gap-1">
                                  <Cpu className="w-3 h-3" />
                                  {msg.model_used}
                                </span>
                              )}
                              {msg.latency_ms && (
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {msg.latency_ms.toFixed(1)}ms
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="p-4 border-t border-gray-800">
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                      placeholder="Type a message..."
                      className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      onClick={handleSend}
                      disabled={!input.trim() || sending}
                      className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-white transition-colors flex items-center gap-2"
                    >
                      {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-40" />
                  <p>Select a conversation or create a new one</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
