'use client';

import { useState, useEffect, useCallback } from 'react';
import { BarChart3, Trophy, Database, Loader2, AlertCircle, Clock, Zap, Hash, CheckCircle2 } from 'lucide-react';

interface BenchmarkEntry {
  model_name: string;
  domain?: string;
  avg_latency_ms: number;
  avg_tokens: number;
  total_queries: number;
  success_rate: number;
}

interface CacheStats {
  total_entries: number;
  hit_rate: number;
  size_mb?: number;
  size?: string;
}

const DOMAIN_COLORS: Record<string, string> = {
  biology: 'bg-green-900/40 text-green-300 border-green-700/50',
  vision: 'bg-purple-900/40 text-purple-300 border-purple-700/50',
  robotics: 'bg-orange-900/40 text-orange-300 border-orange-700/50',
  general: 'bg-cyan-900/40 text-cyan-300 border-cyan-700/50',
  code: 'bg-blue-900/40 text-blue-300 border-blue-700/50',
};

export default function BenchmarksPage() {
  const [leaderboard, setLeaderboard] = useState<BenchmarkEntry[]>([]);
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [benchRes, leaderRes, cacheRes] = await Promise.allSettled([
        fetch('/api/v1/benchmarks'),
        fetch('/api/v1/benchmarks/leaderboard'),
        fetch('/api/v1/cache/stats'),
      ]);

      if (leaderRes.status === 'fulfilled' && leaderRes.value.ok) {
        const data = await leaderRes.value.json();
        const lb = data?.leaderboard;
        setLeaderboard(Array.isArray(lb) ? lb : (Array.isArray(lb?.leaderboard) ? lb.leaderboard : []));
      } else if (benchRes.status === 'fulfilled' && benchRes.value.ok) {
        const data = await benchRes.value.json();
        const b = data?.benchmarks;
        setLeaderboard(Array.isArray(b) ? b : (Array.isArray(b?.stats) ? b.stats : []));
      }

      if (cacheRes.status === 'fulfilled' && cacheRes.value.ok) {
        const data = await cacheRes.value.json();
        setCacheStats(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch benchmark data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getDomainColor = (domain?: string) => {
    return DOMAIN_COLORS[domain || 'general'] || DOMAIN_COLORS.general;
  };

  return (
    <div className="min-h-screen bg-gray-950 pt-14">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
          <BarChart3 className="w-7 h-7 text-cyan-400" />
          Benchmarks & Performance
        </h1>

        {error && (
          <div className="mb-6 bg-red-900/30 border border-red-600 rounded-lg p-3 flex items-center gap-2 text-red-300 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-16 text-gray-400">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" />
            <p>Loading benchmark data...</p>
          </div>
        ) : (
          <div className="space-y-8">
            {cacheStats && (
              <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Database className="w-5 h-5 text-purple-400" />
                  Cache Statistics
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                    <p className="text-sm text-gray-400 mb-1">Total Entries</p>
                    <p className="text-2xl font-bold text-white">{cacheStats.total_entries.toLocaleString()}</p>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                    <p className="text-sm text-gray-400 mb-1">Hit Rate</p>
                    <p className="text-2xl font-bold text-cyan-400">{((cacheStats as any).hit_rate_percent ?? (cacheStats.hit_rate ? cacheStats.hit_rate * 100 : 0)).toFixed(1)}%</p>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                    <p className="text-sm text-gray-400 mb-1">Cache Size</p>
                    <p className="text-2xl font-bold text-white">
                      {cacheStats.size || (cacheStats.size_mb ? `${cacheStats.size_mb.toFixed(1)} MB` : 'N/A')}
                    </p>
                  </div>
                </div>
              </section>
            )}

            <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Trophy className="w-5 h-5 text-amber-400" />
                Model Leaderboard
              </h2>

              {leaderboard.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <BarChart3 className="w-10 h-10 mx-auto mb-3 opacity-40" />
                  <p className="text-lg font-medium mb-1">No benchmark data yet</p>
                  <p className="text-sm">Query data will appear as models are used.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-700">
                        <th className="text-left py-3 px-4 text-gray-400 font-medium">#</th>
                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Model</th>
                        <th className="text-left py-3 px-4 text-gray-400 font-medium">Domain</th>
                        <th className="text-right py-3 px-4 text-gray-400 font-medium flex items-center justify-end gap-1">
                          <Clock className="w-3 h-3" />
                          Avg Latency
                        </th>
                        <th className="text-right py-3 px-4 text-gray-400 font-medium">
                          <span className="flex items-center justify-end gap-1">
                            <Zap className="w-3 h-3" />
                            Avg Tokens
                          </span>
                        </th>
                        <th className="text-right py-3 px-4 text-gray-400 font-medium">
                          <span className="flex items-center justify-end gap-1">
                            <Hash className="w-3 h-3" />
                            Queries
                          </span>
                        </th>
                        <th className="text-right py-3 px-4 text-gray-400 font-medium">
                          <span className="flex items-center justify-end gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            Success
                          </span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {leaderboard.map((entry, idx) => (
                        <tr key={entry.model_name + idx} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                          <td className="py-3 px-4 text-gray-500 font-mono">{idx + 1}</td>
                          <td className="py-3 px-4 text-white font-medium font-mono text-xs">{entry.model_name}</td>
                          <td className="py-3 px-4">
                            <span className={`text-xs px-2 py-0.5 rounded border ${getDomainColor(entry.domain)}`}>
                              {entry.domain || 'general'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right text-gray-300">{entry.avg_latency_ms.toFixed(1)}ms</td>
                          <td className="py-3 px-4 text-right text-gray-300">{entry.avg_tokens.toFixed(0)}</td>
                          <td className="py-3 px-4 text-right text-gray-300">{entry.total_queries.toLocaleString()}</td>
                          <td className="py-3 px-4 text-right">
                            <span className={`font-medium ${entry.success_rate >= 0.95 ? 'text-green-400' : entry.success_rate >= 0.8 ? 'text-amber-400' : 'text-red-400'}`}>
                              {(entry.success_rate * 100).toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
