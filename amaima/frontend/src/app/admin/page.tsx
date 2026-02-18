'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Shield,
  Users,
  Activity,
  DollarSign,
  Database,
  Cpu,
  Clock,
  ArrowLeft,
  RefreshCw,
  LogOut,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface AnalyticsData {
  total_users: number;
  mau: number;
  total_queries: number;
  total_tokens: number;
  estimated_revenue: number;
  tier_distribution: {
    community: number;
    production: number;
    enterprise: number;
  };
  daily_usage: Array<{
    date: string;
    queries: number;
    tokens: number;
  }>;
  model_breakdown: Array<{
    model: string;
    count: number;
    avg_latency: number;
  }>;
  endpoint_breakdown: Array<{
    endpoint: string;
    count: number;
  }>;
  top_users: Array<{
    email: string;
    queries: number;
    tokens: number;
  }>;
}

interface HealthData {
  status: string;
  uptime_seconds: number;
  database: string;
  cache: string;
  nim_api: string;
  active_connections: number;
  memory_usage_mb: number;
}

interface UserData {
  role: string;
}

const API_BASE = '';

export default function AdminPage() {
  const router = useRouter();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const getAuthHeader = () => {
    const token = localStorage.getItem('access_token');
    return token ? `Bearer ${token}` : '';
  };

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: {
          Authorization: getAuthHeader(),
        },
      });

      if (!response.ok) {
        router.push('/login');
        return;
      }

      const data = await response.json();
      const userData: UserData = data.user || data;
      if (userData.role !== 'admin') {
        setError('Access Denied: Admin privileges required');
        setIsAuthorized(false);
        return;
      }

      setIsAuthorized(true);
    } catch (err) {
      console.error('Auth check failed:', err);
      router.push('/login');
    }
  }, [router]);

  const fetchData = useCallback(async () => {
    if (!isAuthorized) return;

    try {
      setRefreshing(true);
      const [analyticsRes, healthRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/admin/analytics`, {
          headers: { Authorization: getAuthHeader() },
        }),
        fetch(`${API_BASE}/api/v1/admin/health`, {
          headers: { Authorization: getAuthHeader() },
        }),
      ]);

      if (!analyticsRes.ok || !healthRes.ok) {
        setError('Failed to fetch data');
        return;
      }

      const [analyticsData, healthData] = await Promise.all([
        analyticsRes.json(),
        healthRes.json(),
      ]);

      setAnalytics(analyticsData);
      setHealth(healthData);
      setError(null);
    } catch (err) {
      console.error('Data fetch failed:', err);
      setError('Failed to fetch dashboard data');
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  }, [isAuthorized]);

  useEffect(() => {
    const initializeAuth = async () => {
      await checkAuth();
    };
    initializeAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (isAuthorized) {
      fetchData();
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthorized, fetchData]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/login');
  };

  if (!isAuthorized && error) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center px-4">
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-8 max-w-md text-center">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-red-400 mb-2">Access Denied</h2>
          <p className="text-red-300 mb-6">{error}</p>
          <button
            onClick={() => {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              router.push('/login');
            }}
            className="w-full px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 font-semibold transition-all"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-300">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const tierColors = {
    community: '#06b6d4',
    production: '#a855f7',
    enterprise: '#ec4899',
  };

  const chartColors = ['#06b6d4', '#a855f7', '#f97316', '#10b981', '#f59e0b'];

  const getStatusColor = (status: string) => {
    return status && status.toLowerCase() === 'healthy'
      ? 'bg-emerald-500'
      : 'bg-red-500';
  };

  const getStatusTextColor = (status: string) => {
    return status && status.toLowerCase() === 'healthy'
      ? 'text-emerald-300'
      : 'text-red-300';
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  return (
    <main className="min-h-screen bg-[#0a0e1a] text-white">
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-full blur-3xl" />
      </div>

      <div className="border-b border-white/10 bg-white/5 backdrop-blur-xl sticky top-0 z-40">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-cyan-400" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              Admin Dashboard
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              disabled={refreshing}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition-all disabled:opacity-50"
              title="Refresh data"
            >
              <RefreshCw
                className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
              />
            </button>
            <a
              href="/"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition-all"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Home</span>
            </a>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:bg-red-500/20 hover:text-red-300 hover:border-red-500/30 transition-all"
            >
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8 space-y-8">
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-400">Total Users</h3>
              <Users className="h-5 w-5 text-cyan-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              {analytics?.total_users.toLocaleString() || '0'}
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-400">MAU</h3>
              <Activity className="h-5 w-5 text-purple-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              {analytics?.mau.toLocaleString() || '0'}
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-400">Total Queries</h3>
              <Activity className="h-5 w-5 text-orange-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              {analytics?.total_queries.toLocaleString() || '0'}
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-slate-400">Est. Revenue</h3>
              <DollarSign className="h-5 w-5 text-emerald-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              ${analytics?.estimated_revenue.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>

        {health && (
          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
              <Cpu className="h-5 w-5 text-cyan-400" />
              System Health
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className={`h-3 w-3 rounded-full ${getStatusColor(
                      health.database
                    )}`}
                  />
                  <span className="text-sm text-slate-400">Database</span>
                </div>
                <div
                  className={`text-lg font-semibold ${getStatusTextColor(
                    health.database
                  )}`}
                >
                  {health.database}
                </div>
              </div>

              <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className={`h-3 w-3 rounded-full ${getStatusColor(
                      health.cache
                    )}`}
                  />
                  <span className="text-sm text-slate-400">Cache</span>
                </div>
                <div
                  className={`text-lg font-semibold ${getStatusTextColor(
                    health.cache
                  )}`}
                >
                  {health.cache}
                </div>
              </div>

              <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className={`h-3 w-3 rounded-full ${getStatusColor(
                      health.nim_api
                    )}`}
                  />
                  <span className="text-sm text-slate-400">NIM API</span>
                </div>
                <div
                  className={`text-lg font-semibold ${getStatusTextColor(
                    health.nim_api
                  )}`}
                >
                  {health.nim_api}
                </div>
              </div>

              <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-400">Memory</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {health.memory_usage_mb.toFixed(0)} MB
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-400">Uptime</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {formatUptime(health.uptime_seconds)}
                </div>
              </div>
              <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-400">Active Connections</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {health.active_connections}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {analytics?.daily_usage && analytics.daily_usage.length > 0 && (
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Daily Usage
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.daily_usage}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" />
                  <YAxis yAxisId="left" stroke="rgba(255,255,255,0.5)" />
                  <YAxis yAxisId="right" orientation="right" stroke="rgba(255,255,255,0.5)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="queries"
                    stroke="#06b6d4"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="tokens"
                    stroke="#a855f7"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {analytics?.tier_distribution && (
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Tier Distribution
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Community', value: analytics.tier_distribution.community },
                      { name: 'Production', value: analytics.tier_distribution.production },
                      { name: 'Enterprise', value: analytics.tier_distribution.enterprise },
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    <Cell fill={tierColors.community} />
                    <Cell fill={tierColors.production} />
                    <Cell fill={tierColors.enterprise} />
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {analytics?.model_breakdown && analytics.model_breakdown.length > 0 && (
          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              Model Usage
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={analytics.model_breakdown.slice(0, 10)}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis type="number" stroke="rgba(255,255,255,0.5)" />
                <YAxis
                  dataKey="model"
                  type="category"
                  width={150}
                  stroke="rgba(255,255,255,0.5)"
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="count" fill="#06b6d4" name="Count" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {analytics?.top_users && analytics.top_users.length > 0 && (
          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Users className="h-5 w-5 text-cyan-400" />
              Top Users
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left px-4 py-3 text-sm font-semibold text-slate-400">
                      Email
                    </th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-slate-400">
                      Queries
                    </th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-slate-400">
                      Tokens
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.top_users.map((user, index) => (
                    <tr
                      key={index}
                      className="border-b border-white/5 hover:bg-white/5 transition-colors"
                    >
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {user.email}
                      </td>
                      <td className="text-right px-4 py-3 text-sm text-slate-300">
                        {user.queries.toLocaleString()}
                      </td>
                      <td className="text-right px-4 py-3 text-sm text-slate-300">
                        {user.tokens.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
