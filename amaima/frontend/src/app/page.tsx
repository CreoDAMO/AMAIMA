'use client';

import { useState, useEffect, useCallback } from 'react';
import { Brain, Zap, Shield, Globe, Sparkles, Send, Loader2, Activity, Cpu, Server, History, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

const API_URL = '';

interface RoutingDecision {
  execution_mode: string;
  model_size: string;
  complexity: string;
  security_level: string;
  confidence: number;
  estimated_latency_ms: number;
  estimated_cost: number;
  reasoning: Record<string, any>;
}

interface QueryResponse {
  response_id: string;
  response_text: string;
  model_used: string;
  routing_decision: RoutingDecision;
  confidence: number;
  latency_ms: number;
  timestamp: string;
}

interface SystemStats {
  total_queries: number;
  uptime_seconds: number;
  active_connections: number;
  version: string;
}

interface HealthStatus {
  status: string;
  version: string;
  components: Record<string, any>;
}

interface ModelInfo {
  id: string;
  name: string;
  params: string;
  latency_ms: number;
  cost_per_1k: number;
  status: string;
}

interface HistoryEntry {
  id: string;
  query: string;
  operation: string;
  complexity: string;
  model: string;
  timestamp: string;
}

const SAMPLE_QUERIES = [
  { text: 'Write a Python function to sort a list using quicksort', operation: 'code_generation', label: 'Python Code' },
  { text: 'Explain quantum computing in simple terms for a beginner', operation: 'analysis', label: 'Explain Concept' },
  { text: 'Translate "Hello, how are you today?" to Spanish, French, and Japanese', operation: 'translation', label: 'Translation' },
  { text: 'Write a haiku about artificial intelligence and human creativity', operation: 'creative', label: 'Creative Writing' },
  { text: 'What is the capital of France?', operation: 'general', label: 'Simple Question' },
];

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [operation, setOperation] = useState<string>('general');
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showModels, setShowModels] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('amaima-query-history');
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load history:', e);
      }
    }
  }, []);

  const saveHistory = (entries: HistoryEntry[]) => {
    const limited = entries.slice(0, 20);
    setHistory(limited);
    localStorage.setItem('amaima-query-history', JSON.stringify(limited));
  };

  const addToHistory = (entry: Omit<HistoryEntry, 'id' | 'timestamp'>) => {
    const newEntry: HistoryEntry = {
      ...entry,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
    };
    saveHistory([newEntry, ...history]);
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('amaima-query-history');
  };

  const fetchStats = useCallback(async () => {
    try {
      const [statsRes, healthRes] = await Promise.all([
        fetch(`/api/v1/stats`),
        fetch(`/api/health`)
      ]);
      
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
      if (healthRes.ok) {
        setHealth(await healthRes.json());
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  const fetchModels = useCallback(async () => {
    setModelsLoading(true);
    try {
      const res = await fetch(`/api/v1/models`);
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
    } finally {
      setModelsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchModels();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [fetchStats, fetchModels]);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    
    setIsSubmitting(true);
    setResponse(null);
    setError(null);
    
    try {
      const res = await fetch(`/api/v1/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          operation,
          preferences: {}
        })
      });
      
      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }
      
      const data: QueryResponse = await res.json();
      setResponse(data);
      
      addToHistory({
        query: query.slice(0, 100),
        operation,
        complexity: data.routing_decision.complexity,
        model: data.model_used,
      });
      
      fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit query');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSampleQuery = (sample: typeof SAMPLE_QUERIES[0]) => {
    setQuery(sample.text);
    setOperation(sample.operation);
  };

  const handleHistoryClick = (entry: HistoryEntry) => {
    setQuery(entry.query);
    setOperation(entry.operation);
    setShowHistory(false);
  };

  const features = [
    { icon: Brain, title: 'Intelligent Routing', description: 'Automatic model selection based on query complexity', color: 'text-cyan-400', bgColor: 'bg-cyan-400/20' },
    { icon: Zap, title: 'Real-time Streaming', description: 'Instant responses with WebSocket streaming', color: 'text-purple-400', bgColor: 'bg-purple-400/20' },
    { icon: Shield, title: 'Secure & Private', description: 'Enterprise-grade security with encrypted storage', color: 'text-emerald-400', bgColor: 'bg-emerald-400/20' },
    { icon: Globe, title: 'Multi-Platform', description: 'Web, mobile, and API access anywhere', color: 'text-pink-400', bgColor: 'bg-pink-400/20' },
  ];

  const operations = [
    { value: 'general', label: 'General', icon: Brain },
    { value: 'code_generation', label: 'Code', icon: Server },
    { value: 'analysis', label: 'Analysis', icon: Activity },
    { value: 'translation', label: 'Translation', icon: Globe },
    { value: 'creative', label: 'Creative', icon: Sparkles },
  ];

  const getComplexityColor = (complexity: string) => {
    const colors: Record<string, string> = {
      TRIVIAL: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      SIMPLE: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      MODERATE: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      COMPLEX: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      EXPERT: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    };
    return colors[complexity] || 'bg-white/10 text-white border-white/20';
  };

  const LoadingSkeleton = () => (
    <div className="space-y-4 mt-6">
      <div className="p-4 rounded-lg bg-white/5 border border-white/10">
        <Skeleton height={24} width={120} baseColor="#1e293b" highlightColor="#334155" className="mb-3" />
        <Skeleton count={3} baseColor="#1e293b" highlightColor="#334155" />
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <Skeleton height={16} width={100} baseColor="#1e293b" highlightColor="#334155" className="mb-3" />
          <Skeleton count={4} height={20} baseColor="#1e293b" highlightColor="#334155" />
        </div>
        <div className="p-4 rounded-lg bg-white/5 border border-white/10">
          <Skeleton height={16} width={120} baseColor="#1e293b" highlightColor="#334155" className="mb-3" />
          <Skeleton count={4} height={20} baseColor="#1e293b" highlightColor="#334155" />
        </div>
      </div>
    </div>
  );

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <section className="relative py-16 px-6 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full blur-3xl" />
        </div>

        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-white/20 bg-white/10 text-white text-xs font-semibold mb-4">
              <Sparkles className="h-3 w-3" />
              Production AI Platform v{health?.version || '5.0.0'}
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-cyan-200 to-purple-200 bg-clip-text text-transparent">
                AMAIMA
              </span>
            </h1>
            
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Advanced Model-Aware Artificial Intelligence Management Interface with intelligent query routing.
            </p>
          </div>

          <div className="mb-16">
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-xl overflow-hidden">
              <div className="p-6 border-b border-white/10">
                <h2 className="flex items-center gap-2 text-xl font-semibold text-white">
                  <Sparkles className="h-5 w-5 text-cyan-400" />
                  Query Interface
                </h2>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex flex-wrap gap-2 mb-4">
                  {operations.map((op) => (
                    <button
                      key={op.value}
                      onClick={() => setOperation(op.value)}
                      className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        operation === op.value
                          ? 'bg-gradient-to-r from-cyan-500 to-purple-500 text-white'
                          : 'bg-white/5 text-slate-300 hover:bg-white/10 border border-white/10'
                      }`}
                    >
                      <op.icon className="h-4 w-4" />
                      {op.label}
                    </button>
                  ))}
                </div>

                <div className="mb-4">
                  <p className="text-sm text-slate-400 mb-2">Try these examples:</p>
                  <div className="flex flex-wrap gap-2">
                    {SAMPLE_QUERIES.map((sample, i) => (
                      <button
                        key={i}
                        onClick={() => handleSampleQuery(sample)}
                        className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-slate-300 transition-all"
                      >
                        {sample.label}
                      </button>
                    ))}
                  </div>
                </div>

                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your query for intelligent routing analysis..."
                  className="w-full min-h-[120px] resize-none text-base bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                  disabled={isSubmitting}
                />

                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-3">
                    <div className={`h-2 w-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className="text-slate-400 text-sm">
                      API: {health?.status || 'Connecting...'}
                    </span>
                    {stats && (
                      <span className="text-slate-500 text-sm">
                        | {stats.total_queries} queries processed
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowHistory(!showHistory)}
                      className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm transition-all"
                    >
                      <History className="h-4 w-4" />
                      History ({history.length})
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={!query.trim() || isSubmitting}
                      className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                      Process Query
                    </button>
                  </div>
                </div>

                {showHistory && history.length > 0 && (
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-semibold text-slate-400">Recent Queries</h4>
                      <button
                        onClick={clearHistory}
                        className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1"
                      >
                        <Trash2 className="h-3 w-3" />
                        Clear
                      </button>
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {history.map((entry) => (
                        <button
                          key={entry.id}
                          onClick={() => handleHistoryClick(entry)}
                          className="w-full text-left p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                        >
                          <p className="text-sm text-white truncate">{entry.query}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`px-1.5 py-0.5 rounded text-xs border ${getComplexityColor(entry.complexity)}`}>
                              {entry.complexity}
                            </span>
                            <span className="text-xs text-slate-500">{entry.model}</span>
                            <span className="text-xs text-slate-600">
                              {new Date(entry.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {error && (
                  <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300">
                    {error}
                  </div>
                )}

                {isSubmitting && <LoadingSkeleton />}

                {response && !isSubmitting && (
                  <div className="space-y-4 mt-6">
                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-white">Response</h3>
                        <span className="text-xs text-slate-400">ID: {response.response_id.slice(0, 8)}...</span>
                      </div>
                      <p className="text-slate-300">{response.response_text}</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                        <h4 className="text-sm font-semibold text-slate-400 mb-3">Routing Decision</h4>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Complexity</span>
                            <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${getComplexityColor(response.routing_decision.complexity)}`}>
                              {response.routing_decision.complexity}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Model</span>
                            <span className="text-white font-mono text-sm">{response.model_used}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Execution Mode</span>
                            <span className="text-cyan-400 text-sm">{response.routing_decision.execution_mode}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Security Level</span>
                            <span className="text-emerald-400 text-sm">{response.routing_decision.security_level}</span>
                          </div>
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                        <h4 className="text-sm font-semibold text-slate-400 mb-3">Performance Metrics</h4>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Confidence</span>
                            <span className="text-white">{(response.confidence * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Actual Latency</span>
                            <span className="text-white">{response.latency_ms.toFixed(2)}ms</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Est. Latency</span>
                            <span className="text-slate-300">{response.routing_decision.estimated_latency_ms.toFixed(2)}ms</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Est. Cost</span>
                            <span className="text-slate-300">${response.routing_decision.estimated_cost.toFixed(6)}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {response.routing_decision.reasoning && (
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                        <h4 className="text-sm font-semibold text-slate-400 mb-3">Routing Reasoning</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                          {Object.entries(response.routing_decision.reasoning).map(([key, value]) => (
                            <div key={key} className="flex flex-col">
                              <span className="text-slate-500 text-xs">{key.replace(/_/g, ' ')}</span>
                              <span className="text-white font-mono">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {features.map((feature, index) => (
              <div key={index} className="group rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-xl p-6 hover:scale-105 transition-all duration-300">
                <div className={`p-3 rounded-xl inline-block mb-4 group-hover:scale-110 transition-transform ${feature.bgColor}`}>
                  <feature.icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-white">{feature.title}</h3>
                <p className="text-sm text-slate-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-12 px-6 border-t border-white/5">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center gap-3 mb-8">
            <Activity className="h-6 w-6 text-cyan-400" />
            <h2 className="text-2xl font-bold text-white">System Status</h2>
          </div>
          
          <div className="grid gap-4 md:grid-cols-4 mb-8">
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">API Status</p>
                  <p className={`text-2xl font-bold ${health?.status === 'healthy' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {health?.status === 'healthy' ? 'Online' : 'Offline'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-emerald-400/20">
                  <Server className="h-6 w-6 text-emerald-400" />
                </div>
              </div>
            </div>
            
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Total Queries</p>
                  <p className="text-2xl font-bold text-cyan-400">{stats?.total_queries || 0}</p>
                </div>
                <div className="p-3 rounded-xl bg-cyan-400/20">
                  <Brain className="h-6 w-6 text-cyan-400" />
                </div>
              </div>
            </div>
            
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Uptime</p>
                  <p className="text-2xl font-bold text-purple-400">
                    {stats ? `${Math.floor(stats.uptime_seconds / 60)}m` : '0m'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-purple-400/20">
                  <Cpu className="h-6 w-6 text-purple-400" />
                </div>
              </div>
            </div>
            
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Active Connections</p>
                  <p className="text-2xl font-bold text-pink-400">{stats?.active_connections || 0}</p>
                </div>
                <div className="p-3 rounded-xl bg-pink-400/20">
                  <Activity className="h-6 w-6 text-pink-400" />
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden">
            <button
              onClick={() => setShowModels(!showModels)}
              className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-all"
            >
              <div className="flex items-center gap-3">
                <Brain className="h-5 w-5 text-cyan-400" />
                <h3 className="text-lg font-semibold text-white">Available Models</h3>
                <span className="text-sm text-slate-400">({models.length} models)</span>
              </div>
              {showModels ? <ChevronUp className="h-5 w-5 text-slate-400" /> : <ChevronDown className="h-5 w-5 text-slate-400" />}
            </button>
            
            {showModels && (
              <div className="p-4 border-t border-white/10">
                {modelsLoading ? (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <div key={i} className="p-3 rounded-lg bg-white/5">
                        <Skeleton height={20} width={120} baseColor="#1e293b" highlightColor="#334155" />
                        <Skeleton height={14} count={2} baseColor="#1e293b" highlightColor="#334155" className="mt-2" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {models.map((model) => (
                      <div key={model.id} className="p-3 rounded-lg bg-white/5 border border-white/10">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold text-white">{model.name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded ${model.status === 'ready' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}`}>
                            {model.status}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 space-y-1">
                          <p>Parameters: {model.params}</p>
                          <p>Latency: ~{model.latency_ms}ms</p>
                          <p>Cost: ${model.cost_per_1k}/1k tokens</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      <footer className="py-8 px-6 border-t border-white/5">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-cyan-400" />
              <span className="font-semibold text-white">AMAIMA</span>
              <span className="text-xs text-slate-500">v{health?.version || '5.0.0'}</span>
            </div>
            <p className="text-sm text-slate-400">
              Production-Ready AI Query Platform
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
