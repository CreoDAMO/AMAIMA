'use client';

import { useState, useEffect, useCallback } from 'react';
import { Brain, Zap, Shield, Globe, Sparkles, Send, Loader2, Activity, Cpu, HardDrive, Server } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [operation, setOperation] = useState<string>('general');

  const fetchStats = useCallback(async () => {
    try {
      const [statsRes, healthRes] = await Promise.all([
        fetch(`${API_URL}/v1/stats`),
        fetch(`${API_URL}/health`)
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

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    
    setIsSubmitting(true);
    setResponse(null);
    setError(null);
    
    try {
      const res = await fetch(`${API_URL}/v1/query`, {
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
      fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit query');
    } finally {
      setIsSubmitting(false);
    }
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

                  <button
                    onClick={handleSubmit}
                    disabled={!query.trim() || isSubmitting}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    Process Query
                  </button>
                </div>

                {error && (
                  <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300">
                    {error}
                  </div>
                )}

                {response && (
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
          
          <div className="grid gap-4 md:grid-cols-4">
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
