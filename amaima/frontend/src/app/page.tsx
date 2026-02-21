'use client';

import { useState, useEffect, useCallback } from 'react';
import { Brain, Zap, Shield, Globe, Sparkles, Send, Loader2, Activity, Cpu, Server, History, Trash2, ChevronDown, ChevronUp, Microscope, Bot, Eye, Users, LogIn, Settings } from 'lucide-react';
import Link from 'next/link';
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
  params?: string;
  parameters?: string;
  provider?: string;
  context_window?: number;
  domain?: string;
  category?: string;
  description?: string;
  latency_ms?: number;
  cost_per_1k?: number;
  status: string;
  api_status?: string;
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
  { text: 'Design a drug targeting the EGFR receptor with high selectivity', operation: 'biology', label: 'Drug Discovery' },
  { text: 'Navigate robot to pick up the red box from shelf B3', operation: 'robotics', label: 'Robot Navigation' },
  { text: 'Analyze the warehouse scene for safety hazards and obstacles', operation: 'vision', label: 'Scene Analysis' },
  { text: 'Research the latest advances in protein folding prediction', operation: 'agents', label: 'Agent Research' },
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
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => { setCopied(false); }, [response]);

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
        setModels(data.available_models || data.models || []);
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
      let res: Response;

      if (operation === 'biology') {
        const formData = new FormData();
        formData.append('query', query);
        formData.append('task_type', 'general');
        res = await fetch(`/api/v1/biology?endpoint=query`, { method: 'POST', body: formData });
      } else if (operation === 'robotics') {
        res = await fetch(`/api/v1/robotics?endpoint=plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, robot_type: 'amr' }),
        });
      } else if (operation === 'vision') {
        const formData = new FormData();
        formData.append('query', query);
        res = await fetch(`/api/v1/vision?endpoint=reason`, { method: 'POST', body: formData });
      } else if (operation === 'agents') {
        res = await fetch(`/api/v1/agents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task: query, crew_type: 'research', process: 'sequential' }),
        });
      } else if (useStreaming) {
        setIsStreaming(true);
        setStreamingText('');
        let fullText = '';
        let streamModel = '';

        try {
          const streamRes = await fetch(`/api/v1/query/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, operation, preferences: {} }),
          });

          if (!streamRes.ok) {
            const errBody = await streamRes.json().catch(() => null);
            const errMsg = errBody?.detail || errBody?.error || `Stream error: ${streamRes.status}`;
            throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg));
          }

          const reader = streamRes.body?.getReader();
          const decoder = new TextDecoder();
          if (!reader) throw new Error('No stream reader');

          let buffer = '';
          let currentEvent = '';
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
              if (line.startsWith('event: ')) {
                currentEvent = line.slice(7).trim();
              } else if (line.startsWith('data: ')) {
                try {
                  const parsed = JSON.parse(line.slice(6));
                  if (currentEvent === 'error') {
                    throw new Error(parsed.error || 'Stream error');
                  }
                  if (currentEvent === 'token' && parsed.content) {
                    fullText += parsed.content;
                    setStreamingText(fullText);
                  }
                  if (parsed.model) streamModel = parsed.model;
                  if (currentEvent === 'done') break;
                } catch (e) {
                  if (e instanceof Error && e.message !== 'Stream error') {} else throw e;
                }
                currentEvent = '';
              } else if (line.trim() === '') {
                currentEvent = '';
              }
            }
          }

          const streamResponse: QueryResponse = {
            response_id: 'stream-' + Date.now(),
            response_text: fullText || 'No response received',
            model_used: streamModel || 'streaming',
            routing_decision: { execution_mode: 'streaming', model_size: 'N/A', complexity: 'N/A', security_level: 'standard', confidence: 0.9, estimated_latency_ms: 0, estimated_cost: 0, reasoning: {} },
            confidence: 0.9,
            latency_ms: 0,
            timestamp: new Date().toISOString(),
          };
          setResponse(streamResponse);
          setStreamingText('');
          addToHistory({ query: query.slice(0, 100), operation, complexity: 'STREAMED', model: streamModel || 'streaming' });
        } finally {
          setIsStreaming(false);
        }
        setIsSubmitting(false);
        fetchStats();
        return;
      } else {
        res = await fetch(`/api/v1/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, operation, preferences: {} }),
        });
      }
      
      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        const errMsg = errData?.detail || errData?.error || `API error: ${res.status}`;
        throw new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg));
      }
      
      const data = await res.json();

      if (['biology', 'robotics', 'vision', 'agents'].includes(operation)) {
        const domainResponse: QueryResponse = {
          response_id: data.crew || data.service || 'domain-' + Date.now(),
          response_text: data.response || data.final_output || data.plan || data.predicted_outcome || (typeof data === 'object' ? JSON.stringify(data, null, 2) : String(data)),
          model_used: data.model || data.agents_used?.join(', ') || operation,
          routing_decision: {
            execution_mode: data.execution_mode || data.process || 'domain_specific',
            model_size: 'N/A',
            complexity: 'DOMAIN',
            security_level: 'standard',
            confidence: data.domain_confidence || 0.9,
            estimated_latency_ms: data.latency_ms || data.total_latency_ms || 0,
            estimated_cost: data.cost_usd || 0,
            reasoning: { domain: operation, service: data.service || data.crew || operation },
          },
          confidence: 0.9,
          latency_ms: data.latency_ms || data.total_latency_ms || 0,
          timestamp: new Date().toISOString(),
        };
        setResponse(domainResponse);
        addToHistory({
          query: query.slice(0, 100),
          operation,
          complexity: 'DOMAIN',
          model: domainResponse.model_used,
        });
      } else {
        const queryResponse: QueryResponse = {
          response_id: data.response_id || data.query_hash || 'query-' + Date.now(),
          response_text: data.response_text || data.output || 'No response',
          model_used: data.model_used || data.model || 'unknown',
          routing_decision: data.routing_decision || {
            execution_mode: data.execution_mode || 'standard',
            model_size: 'N/A',
            complexity: data.complexity_level || 'UNKNOWN',
            security_level: 'standard',
            confidence: data.confidence?.overall || 0,
            estimated_latency_ms: data.actual_latency_ms || 0,
            estimated_cost: data.actual_cost_usd || 0,
            reasoning: data.reasons || {},
          },
          confidence: data.confidence?.overall || data.confidence || 0,
          latency_ms: data.actual_latency_ms || data.latency_ms || 0,
          timestamp: data.timestamp || new Date().toISOString(),
        };
        setResponse(queryResponse);
        addToHistory({
          query: query.slice(0, 100),
          operation,
          complexity: queryResponse.routing_decision?.complexity || data.complexity_level || 'UNKNOWN',
          model: queryResponse.model_used,
        });
      }
      
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
    { icon: Brain, title: 'Intelligent Routing', description: 'Automatic model selection with domain-aware classification', color: 'text-cyan-400', bgColor: 'bg-cyan-400/20' },
    { icon: Microscope, title: 'Drug Discovery', description: 'BioNeMo-powered molecular generation and protein analysis', color: 'text-green-400', bgColor: 'bg-green-400/20' },
    { icon: Bot, title: 'Robotics / Physical AI', description: 'ROS2/Isaac robot planning, navigation, and simulation', color: 'text-orange-400', bgColor: 'bg-orange-400/20' },
    { icon: Eye, title: 'Vision & Reasoning', description: 'Cosmos R2 embodied reasoning and multimodal analysis', color: 'text-purple-400', bgColor: 'bg-purple-400/20' },
    { icon: Users, title: 'Multi-Agent Crews', description: 'CrewAI-based agent orchestration for complex tasks', color: 'text-pink-400', bgColor: 'bg-pink-400/20' },
    { icon: Shield, title: 'Secure & Extensible', description: 'Plugin architecture with enterprise-grade security', color: 'text-emerald-400', bgColor: 'bg-emerald-400/20' },
  ];

  const operations = [
    { value: 'general', label: 'General', icon: Brain },
    { value: 'code_generation', label: 'Code', icon: Server },
    { value: 'analysis', label: 'Analysis', icon: Activity },
    { value: 'biology', label: 'Biology', icon: Microscope },
    { value: 'robotics', label: 'Robotics', icon: Bot },
    { value: 'vision', label: 'Vision', icon: Eye },
    { value: 'agents', label: 'Agents', icon: Users },
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
              Advanced AI Orchestration Platform with intelligent routing, multi-agent crews, drug discovery, robotics, and vision reasoning.
            </p>

            <div className="flex items-center justify-center gap-3 mt-6">
              <Link href="/login" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm transition-all">
                <LogIn className="h-4 w-4" />
                Login
              </Link>
              <Link href="/admin" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm transition-all">
                <Settings className="h-4 w-4" />
                Admin
              </Link>
              <Link href="/billing" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm transition-all">
                <Zap className="h-4 w-4" />
                Billing
              </Link>
              <Link href="/agent-builder" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm transition-all">
                <Cpu className="h-4 w-4" />
                Agent Builder
              </Link>
              <Link href="/fhe" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-sm transition-all">
                <Shield className="h-4 w-4" />
                FHE Encryption
              </Link>
            </div>
          </div>

          <div className="mb-8">
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
                      {models.map((model) => {
                        const domainColors: Record<string, string> = {
                          general: 'bg-blue-500/20 text-blue-300',
                          vision: 'bg-purple-500/20 text-purple-300',
                          biology: 'bg-green-500/20 text-green-300',
                          robotics: 'bg-orange-500/20 text-orange-300',
                          speech: 'bg-pink-500/20 text-pink-300',
                          embedding: 'bg-teal-500/20 text-teal-300',
                          molecular: 'bg-emerald-500/20 text-emerald-300',
                        };
                        const domainColor = domainColors[model.domain || 'general'] || domainColors.general;
                        const statusStyle = model.status === 'available' || model.status === 'ready'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : model.status === 'catalog'
                          ? 'bg-sky-500/20 text-sky-300'
                          : 'bg-amber-500/20 text-amber-300';
                        return (
                          <div key={model.id} className="p-3 rounded-lg bg-white/5 border border-white/10">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-semibold text-white text-sm">{model.name}</span>
                              <span className={`text-xs px-2 py-0.5 rounded ${statusStyle}`}>
                                {model.status === 'catalog' ? 'self-hosted' : model.status}
                              </span>
                            </div>
                            <div className="flex gap-1.5 mb-2">
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${domainColor}`}>
                                {model.domain || 'general'}
                              </span>
                              {model.category && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-slate-300">
                                  {model.category}
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-400 space-y-1">
                              <p>Parameters: {model.parameters || model.params || 'N/A'}</p>
                              {model.context_window && <p>Context: {(model.context_window / 1000).toFixed(0)}k tokens</p>}
                              {model.provider && <p>Provider: {model.provider}</p>}
                              {model.description && <p className="text-slate-500 mt-1">{model.description}</p>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
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
                    <label className="inline-flex items-center gap-2 px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={useStreaming}
                        onChange={(e) => setUseStreaming(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-8 h-4 rounded-full bg-slate-600 peer-checked:bg-cyan-500 relative transition-colors">
                        <div className="absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
                      </div>
                      Stream
                    </label>
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

                {isStreaming && streamingText && (
                  <div className="mt-6 p-4 rounded-lg bg-white/5 border border-cyan-500/30">
                    <div className="flex items-center gap-2 mb-3">
                      <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                      <h3 className="text-lg font-semibold text-cyan-400">Streaming Response...</h3>
                    </div>
                    <p className="text-slate-300 whitespace-pre-wrap">{streamingText}<span className="inline-block w-2 h-5 bg-cyan-400 animate-pulse ml-0.5" /></p>
                  </div>
                )}

                {response && !isSubmitting && !isStreaming && (
                  <div className="space-y-4 mt-6">
                    <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-white">Response</h3>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(response.response_text).then(() => {
                                setCopied(true);
                                setTimeout(() => setCopied(false), 2000);
                              }).catch(() => {});
                            }}
                            className="px-2 py-1 text-xs rounded bg-white/10 hover:bg-white/20 text-slate-300 border border-white/10 transition-colors"
                          >
                            {copied ? 'Copied!' : 'Copy'}
                          </button>
                          <span className="text-xs text-slate-400">ID: {response.response_id.slice(0, 8)}...</span>
                        </div>
                      </div>
                      <p className="text-slate-300 whitespace-pre-wrap select-text">{response.response_text}</p>
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

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
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
            <div className="flex items-center gap-4">
              <a href="/billing" className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
                Billing & API Keys
              </a>
              <p className="text-sm text-slate-400">
                Production-Ready AI Query Platform
              </p>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
