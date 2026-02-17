'use client';

import { useState, useEffect, useCallback } from 'react';
import { CreditCard, Key, BarChart3, ArrowUpRight, Shield, Zap, Crown, ChevronLeft, Copy, Check, Loader2, AlertCircle, TrendingUp, Database, Activity } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import Link from 'next/link';

interface TierInfo {
  name: string;
  description: string;
  queries_per_month: number;
}

interface UsageStats {
  api_key_id: string;
  tier: string;
  tier_name: string;
  month: string;
  queries_used: number;
  queries_limit: number;
  tokens_used: number;
  email: string | null;
  stripe_customer_id: string | null;
}

interface ApiKeyInfo {
  id: string;
  key_prefix: string;
  user_email: string | null;
  tier: string;
  is_active: boolean;
  created_at: string;
}

interface StripeProduct {
  id: string;
  name: string;
  description: string;
  metadata: Record<string, string>;
  prices: Array<{
    id: string;
    unit_amount: number;
    currency: string;
    recurring: any;
  }>;
}

interface AnalyticsData {
  daily_usage: Array<{ day: string; queries: number; tokens: number; avg_latency: number; success_rate: number }>;
  model_breakdown: Array<{ model: string; count: number; tokens: number }>;
  endpoint_breakdown: Array<{ endpoint: string; count: number; avg_latency: number }>;
  tier_distribution: Array<{ tier: string; count: number }>;
  cache_stats: { hits: number; misses: number; hit_rate: number; size: number; estimated_latency_savings_pct: number };
  period: string;
}

const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#f97316', '#14b8a6', '#6366f1'];

const TIER_FEATURES: Record<string, string[]> = {
  community: [
    '1,000 queries/month',
    'All 14 NVIDIA NIM models',
    'Basic routing',
    'Community support',
  ],
  production: [
    '10,000 queries/month',
    'All 14 NVIDIA NIM models',
    'Priority routing',
    'All domain services',
    'Email support',
  ],
  enterprise: [
    'Unlimited queries',
    'All 14 NVIDIA NIM models',
    'Custom SLA',
    'Dedicated support',
    'Advanced analytics',
    'Custom model routing',
  ],
};

const TIER_ICONS: Record<string, any> = {
  community: Shield,
  production: Zap,
  enterprise: Crown,
};

const TIER_COLORS: Record<string, string> = {
  community: 'border-gray-600 bg-gray-800/50',
  production: 'border-blue-500 bg-blue-900/30',
  enterprise: 'border-amber-500 bg-amber-900/30',
};

const TIER_PRICING: Record<string, { amount: number; label: string }> = {
  community: { amount: 0, label: 'Free' },
  production: { amount: 49, label: '$49' },
  enterprise: { amount: 299, label: '$299' },
};

export default function BillingPage() {
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [products, setProducts] = useState<StripeProduct[]>([]);
  const [tiers, setTiers] = useState<Record<string, TierInfo>>({});
  const [newKeyEmail, setNewKeyEmail] = useState('');
  const [newKeyResult, setNewKeyResult] = useState<any>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [checkingOut, setCheckingOut] = useState<string | null>(null);
  const [selectedKeyId, setSelectedKeyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics'>('overview');
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      setSuccessMsg('Subscription activated! Your tier has been upgraded.');
    }
    if (params.get('canceled') === 'true') {
      setError('Checkout was canceled. No changes were made.');
    }
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [keysRes, tiersRes, productsRes] = await Promise.all([
        fetch('/api/v1/billing?path=api-keys'),
        fetch('/api/v1/billing?path=tiers'),
        fetch('/api/stripe/products'),
      ]);

      const keysData = await keysRes.json();
      const tiersData = await tiersRes.json();
      const productsData = await productsRes.json();

      setApiKeys(keysData.api_keys || []);
      setTiers(tiersData.tiers || {});
      setProducts(productsData.data || []);

      if (keysData.api_keys?.length > 0) {
        const firstKey = keysData.api_keys[0];
        setSelectedKeyId(firstKey.id);
        const usageRes = await fetch(`/api/v1/billing?path=usage/${firstKey.id}`);
        const usageData = await usageRes.json();
        setUsage(usageData);
      }
    } catch (err: any) {
      console.error('Failed to fetch billing data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const createApiKey = async () => {
    setCreating(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/billing?path=api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newKeyEmail || undefined, tier: 'community' }),
      });
      const data = await res.json();
      if (data.api_key) {
        setNewKeyResult(data);
        setNewKeyEmail('');
        fetchData();
      } else {
        setError('Failed to create API key');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const copyApiKey = async (key: string) => {
    await navigator.clipboard.writeText(key);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const selectKey = async (keyId: string) => {
    setSelectedKeyId(keyId);
    try {
      const usageRes = await fetch(`/api/v1/billing?path=usage/${keyId}`);
      const usageData = await usageRes.json();
      setUsage(usageData);
    } catch (err) {
      console.error('Failed to fetch usage:', err);
    }
  };

  const handleCheckout = async (priceId: string) => {
    setCheckingOut(priceId);
    setError(null);
    try {
      const res = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          priceId,
          apiKeyId: selectedKeyId,
          email: newKeyEmail || usage?.email || '',
        }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError(data.error || 'Failed to create checkout session');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCheckingOut(null);
    }
  };

  const handlePortal = async () => {
    if (!usage?.stripe_customer_id) return;
    try {
      const res = await fetch('/api/stripe/portal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customerId: usage.stripe_customer_id }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fetchAnalytics = useCallback(async () => {
    setAnalyticsLoading(true);
    try {
      const url = selectedKeyId
        ? `/api/v1/billing/analytics?api_key_id=${selectedKeyId}`
        : '/api/v1/billing/analytics';
      const res = await fetch(url);
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setAnalyticsLoading(false);
    }
  }, [selectedKeyId]);

  useEffect(() => {
    if (activeTab === 'analytics' && !analytics) {
      fetchAnalytics();
    }
  }, [activeTab, analytics, fetchAnalytics]);

  const usagePercent = usage && usage.queries_limit > 0 && usage.queries_used != null
    ? Math.min(100, (usage.queries_used / usage.queries_limit) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white">
      <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
              <ChevronLeft className="w-4 h-4" />
              <span className="text-sm">Back to Dashboard</span>
            </Link>
            <div className="h-6 w-px bg-gray-700" />
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Billing & API Keys
            </h1>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <div className="flex gap-1 bg-gray-900/60 border border-gray-800 rounded-lg p-1 w-fit">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'overview' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            <CreditCard className="w-4 h-4 inline mr-2" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'analytics' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            <TrendingUp className="w-4 h-4 inline mr-2" />
            Analytics
          </button>
        </div>

        {successMsg && (
          <div className="bg-green-900/30 border border-green-600 rounded-lg p-4 flex items-center gap-3">
            <Check className="w-5 h-5 text-green-400" />
            <span className="text-green-300">{successMsg}</span>
            <button onClick={() => setSuccessMsg(null)} className="ml-auto text-green-400 hover:text-green-200">Dismiss</button>
          </div>
        )}
        {error && (
          <div className="bg-red-900/30 border border-red-600 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-300">{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200">Dismiss</button>
          </div>
        )}

        {activeTab === 'analytics' && (
          <section className="space-y-6">
            {analyticsLoading ? (
              <div className="text-center py-12 text-gray-400">
                <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin" />
                Loading analytics...
              </div>
            ) : analytics ? (
              <>
                <div className="grid md:grid-cols-4 gap-4">
                  <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
                    <p className="text-xs text-gray-400 mb-1">Cache Hit Rate</p>
                    <p className="text-2xl font-bold text-blue-400">{analytics.cache_stats?.hit_rate ?? 0}%</p>
                    <p className="text-[10px] text-gray-500 mt-1">
                      {analytics.cache_stats?.hits ?? 0} hits / {(analytics.cache_stats?.hits ?? 0) + (analytics.cache_stats?.misses ?? 0)} total
                    </p>
                  </div>
                  <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
                    <p className="text-xs text-gray-400 mb-1">Est. Latency Savings</p>
                    <p className="text-2xl font-bold text-green-400">{analytics.cache_stats?.estimated_latency_savings_pct ?? 0}%</p>
                    <p className="text-[10px] text-gray-500 mt-1">From NIM prompt caching</p>
                  </div>
                  <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
                    <p className="text-xs text-gray-400 mb-1">Total Queries (30d)</p>
                    <p className="text-2xl font-bold text-purple-400">
                      {analytics.daily_usage.reduce((s, d) => s + d.queries, 0).toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
                    <p className="text-xs text-gray-400 mb-1">Total Tokens (30d)</p>
                    <p className="text-2xl font-bold text-amber-400">
                      {analytics.daily_usage.reduce((s, d) => s + d.tokens, 0).toLocaleString()}
                    </p>
                  </div>
                </div>

                {analytics.daily_usage.length > 0 && (
                  <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                      <Activity className="w-4 h-4 text-blue-400" />
                      Daily Query Volume
                    </h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={analytics.daily_usage}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 10 }} tickFormatter={(v: string) => v.slice(5)} />
                          <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} />
                          <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} />
                          <Bar dataKey="queries" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {analytics.daily_usage.length > 0 && (
                  <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-400" />
                      Latency Trend (ms)
                    </h3>
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={analytics.daily_usage}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 10 }} tickFormatter={(v: string) => v.slice(5)} />
                          <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} />
                          <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} />
                          <Line type="monotone" dataKey="avg_latency" stroke="#10b981" strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                <div className="grid md:grid-cols-2 gap-6">
                  {analytics.model_breakdown.length > 0 && (
                    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                      <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                        <Database className="w-4 h-4 text-purple-400" />
                        Model Usage
                      </h3>
                      <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie data={analytics.model_breakdown} dataKey="count" nameKey="model" cx="50%" cy="50%" outerRadius={70} label={({ name }: { name: string }) => name.split('/').pop()}>
                              {analytics.model_breakdown.map((_: any, i: number) => (
                                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {analytics.endpoint_breakdown.length > 0 && (
                    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                      <h3 className="text-sm font-semibold text-gray-300 mb-4">Endpoint Usage</h3>
                      <div className="space-y-2">
                        {analytics.endpoint_breakdown.map((ep, i) => (
                          <div key={i} className="flex items-center justify-between text-sm">
                            <code className="text-xs text-gray-400">{ep.endpoint}</code>
                            <div className="flex items-center gap-3">
                              <span className="text-gray-300">{ep.count} calls</span>
                              <span className="text-gray-500">{ep.avg_latency}ms avg</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {analytics.tier_distribution.length > 0 && (
                  <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4">Active Keys by Tier</h3>
                    <div className="flex gap-6">
                      {analytics.tier_distribution.map((t, i) => (
                        <div key={i} className="text-center">
                          <p className="text-2xl font-bold" style={{ color: PIE_COLORS[i % PIE_COLORS.length] }}>{t.count}</p>
                          <p className="text-xs text-gray-400 capitalize">{t.tier}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={fetchAnalytics}
                  className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <Activity className="w-3 h-3" /> Refresh Analytics
                </button>
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                No analytics data available yet. Start making API queries to see statistics.
              </div>
            )}
          </section>
        )}

        {activeTab === 'overview' && usage && (
          <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                Usage This Month
              </h2>
              <span className="text-sm text-gray-400">{usage.month}</span>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Queries Used</span>
                <span className="font-medium">
                  {(usage.queries_used ?? 0).toLocaleString()} / {usage.queries_limit === -1 ? 'Unlimited' : (usage.queries_limit ?? 0).toLocaleString()}
                </span>
              </div>
              {usage.queries_limit > 0 && (
                <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      usagePercent > 90 ? 'bg-red-500' : usagePercent > 70 ? 'bg-yellow-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${usagePercent}%` }}
                  />
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Tokens Used</span>
                <span className="font-medium">{(usage.tokens_used ?? 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Current Tier</span>
                <span className="font-medium capitalize px-2 py-0.5 rounded bg-gray-800">
                  {usage.tier_name}
                </span>
              </div>
              {usage.stripe_customer_id && (
                <button
                  onClick={handlePortal}
                  className="mt-2 text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  Manage Subscription <ArrowUpRight className="w-3 h-3" />
                </button>
              )}
            </div>
          </section>
        )}

        {activeTab === 'overview' && <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Key className="w-5 h-5 text-purple-400" />
            API Keys
          </h2>

          {newKeyResult && (
            <div className="mb-4 bg-green-900/20 border border-green-700 rounded-lg p-4">
              <p className="text-sm text-green-300 mb-2">API Key created! Copy it now - it won't be shown again.</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-gray-950 px-3 py-2 rounded text-sm font-mono text-green-400 break-all">
                  {newKeyResult.api_key}
                </code>
                <button
                  onClick={() => copyApiKey(newKeyResult.api_key)}
                  className="p-2 hover:bg-gray-700 rounded transition-colors"
                >
                  {copiedKey ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-400" />}
                </button>
              </div>
              <button onClick={() => setNewKeyResult(null)} className="mt-2 text-sm text-gray-400 hover:text-gray-200">
                Dismiss
              </button>
            </div>
          )}

          <div className="flex gap-3 mb-4">
            <input
              type="email"
              placeholder="Email (optional)"
              value={newKeyEmail}
              onChange={(e) => setNewKeyEmail(e.target.value)}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={createApiKey}
              disabled={creating}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
              Generate Key
            </button>
          </div>

          {loading ? (
            <div className="text-center py-8 text-gray-400">Loading...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Key className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No API keys yet. Generate one to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {apiKeys.map((key) => (
                <button
                  key={key.id}
                  onClick={() => selectKey(key.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedKeyId === key.id
                      ? 'border-blue-500 bg-blue-900/20'
                      : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <code className="text-sm font-mono text-gray-300">{key.key_prefix}...</code>
                      <span className={`text-xs px-2 py-0.5 rounded capitalize ${
                        key.tier === 'enterprise' ? 'bg-amber-900/50 text-amber-300' :
                        key.tier === 'production' ? 'bg-blue-900/50 text-blue-300' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {key.tier}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${key.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                      <span className="text-xs text-gray-500">
                        {new Date(key.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  {key.user_email && (
                    <p className="text-xs text-gray-500 mt-1">{key.user_email}</p>
                  )}
                </button>
              ))}
            </div>
          )}
        </section>}

        {activeTab === 'overview' && <section>
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <CreditCard className="w-5 h-5 text-green-400" />
            Plans
          </h2>
          <div className="grid md:grid-cols-3 gap-4">
            {['community', 'production', 'enterprise'].map((tierKey) => {
              const Icon = TIER_ICONS[tierKey] || Shield;
              const features = TIER_FEATURES[tierKey] || [];
              const product = products.find((p) => p.metadata?.tier === tierKey);
              const price = product?.prices?.[0];
              const isCurrentTier = usage?.tier === tierKey;

              return (
                <div
                  key={tierKey}
                  className={`rounded-xl border p-6 flex flex-col ${TIER_COLORS[tierKey]} ${
                    isCurrentTier ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`w-5 h-5 ${
                      tierKey === 'enterprise' ? 'text-amber-400' :
                      tierKey === 'production' ? 'text-blue-400' :
                      'text-gray-400'
                    }`} />
                    <h3 className="font-semibold capitalize">{tierKey}</h3>
                  </div>
                  <div className="mb-4">
                    {price ? (
                      <div>
                        <span className="text-3xl font-bold">${(price.unit_amount / 100).toFixed(0)}</span>
                        <span className="text-gray-400 text-sm">/month</span>
                      </div>
                    ) : (
                      <div>
                        <span className="text-3xl font-bold">{TIER_PRICING[tierKey]?.label || 'Free'}</span>
                        {TIER_PRICING[tierKey]?.amount > 0 && (
                          <span className="text-gray-400 text-sm">/month</span>
                        )}
                      </div>
                    )}
                  </div>
                  <ul className="space-y-2 mb-6 flex-1">
                    {features.map((f, i) => (
                      <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                        <Check className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  {isCurrentTier ? (
                    <div className="text-center py-2 text-sm text-blue-400 border border-blue-500/30 rounded-lg bg-blue-900/20">
                      Current Plan
                    </div>
                  ) : price ? (
                    <button
                      onClick={() => handleCheckout(price.id)}
                      disabled={!!checkingOut || !selectedKeyId}
                      className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                    >
                      {checkingOut === price.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <ArrowUpRight className="w-4 h-4" />
                          Upgrade
                        </>
                      )}
                    </button>
                  ) : tierKey === 'community' ? (
                    <div className="text-center py-2 text-sm text-gray-500 border border-gray-600/30 rounded-lg">
                      Free tier
                    </div>
                  ) : tierKey === 'enterprise' ? (
                    <div className="text-center py-2 text-sm text-amber-400/80 border border-amber-500/30 rounded-lg bg-amber-900/10 cursor-pointer hover:bg-amber-900/20 transition-colors">
                      Contact Sales
                    </div>
                  ) : (
                    <div className="text-center py-2 text-sm text-blue-400 border border-blue-500/30 rounded-lg bg-blue-900/10 cursor-pointer hover:bg-blue-900/20 transition-colors">
                      <ArrowUpRight className="w-4 h-4 inline mr-1" />
                      Upgrade
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>}
      </main>
    </div>
  );
}
