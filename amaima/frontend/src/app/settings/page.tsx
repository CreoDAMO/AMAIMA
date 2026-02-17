'use client';

import { useState, useEffect, useCallback } from 'react';
import { Settings, Building2, Webhook, FlaskConical, Route, Plus, Loader2, AlertCircle, Key, Trash2, CheckCircle2 } from 'lucide-react';

type TabKey = 'organizations' | 'webhooks' | 'experiments' | 'routing';

interface Organization {
  id: string;
  name: string;
  created_at: string;
}

interface WebhookEntry {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  created_at: string;
}

interface Experiment {
  id: string;
  name: string;
  model_a: string;
  model_b: string;
  description?: string;
  status: string;
  created_at: string;
}

interface RoutingRule {
  id: string;
  name: string;
  preferred_model: string;
  domain?: string;
  min_complexity?: number;
  max_complexity?: number;
  created_at: string;
}

const TABS: { key: TabKey; label: string; icon: any }[] = [
  { key: 'organizations', label: 'Organizations', icon: Building2 },
  { key: 'webhooks', label: 'Webhooks', icon: Webhook },
  { key: 'experiments', label: 'Experiments', icon: FlaskConical },
  { key: 'routing', label: 'Routing Rules', icon: Route },
];

const WEBHOOK_EVENTS = [
  'query.completed',
  'query.failed',
  'model.switched',
  'billing.usage_limit',
  'experiment.completed',
];

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-900/40 text-green-300 border-green-700/50',
  running: 'bg-cyan-900/40 text-cyan-300 border-cyan-700/50',
  completed: 'bg-purple-900/40 text-purple-300 border-purple-700/50',
  paused: 'bg-amber-900/40 text-amber-300 border-amber-700/50',
  draft: 'bg-gray-700/40 text-gray-300 border-gray-600/50',
};

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('organizations');
  const [needsAuth, setNeedsAuth] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [newOrgName, setNewOrgName] = useState('');

  const [webhooks, setWebhooks] = useState<WebhookEntry[]>([]);
  const [newWebhookUrl, setNewWebhookUrl] = useState('');
  const [newWebhookEvents, setNewWebhookEvents] = useState<string[]>([]);

  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [newExpName, setNewExpName] = useState('');
  const [newExpModelA, setNewExpModelA] = useState('');
  const [newExpModelB, setNewExpModelB] = useState('');
  const [newExpDesc, setNewExpDesc] = useState('');

  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [newRuleName, setNewRuleName] = useState('');
  const [newRuleModel, setNewRuleModel] = useState('');
  const [newRuleDomain, setNewRuleDomain] = useState('');
  const [newRuleMinComplexity, setNewRuleMinComplexity] = useState('');
  const [newRuleMaxComplexity, setNewRuleMaxComplexity] = useState('');

  const fetchTabData = useCallback(async (tab: TabKey) => {
    setLoading(true);
    setError(null);
    try {
      let endpoint = '';
      switch (tab) {
        case 'organizations': endpoint = '/api/v1/organizations'; break;
        case 'webhooks': endpoint = '/api/v1/webhooks'; break;
        case 'experiments': endpoint = '/api/v1/experiments'; break;
        case 'routing': endpoint = '/api/v1/routing-rules'; break;
      }
      const res = await fetch(endpoint);
      if (res.status === 401 || res.status === 403) {
        setNeedsAuth(true);
        setLoading(false);
        return;
      }
      if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
      const data = await res.json();
      switch (tab) {
        case 'organizations': setOrgs(data.organizations || data || []); break;
        case 'webhooks': setWebhooks(data.webhooks || data || []); break;
        case 'experiments': setExperiments(data.experiments || data || []); break;
        case 'routing': setRules(data.rules || data.routing_rules || data || []); break;
      }
    } catch (err: any) {
      setNeedsAuth(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTabData(activeTab);
  }, [activeTab, fetchTabData]);

  const showSuccess = (msg: string) => {
    setSuccess(msg);
    setTimeout(() => setSuccess(null), 3000);
  };

  const handleCreateOrg = async () => {
    if (!newOrgName.trim()) return;
    setSaving(true);
    try {
      const res = await fetch('/api/v1/organizations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newOrgName }),
      });
      if (res.ok) {
        setNewOrgName('');
        showSuccess('Organization created');
        fetchTabData('organizations');
      } else {
        setError('Failed to create organization');
      }
    } catch { setError('Failed to create organization'); }
    finally { setSaving(false); }
  };

  const handleCreateWebhook = async () => {
    if (!newWebhookUrl.trim()) return;
    setSaving(true);
    try {
      const res = await fetch('/api/v1/webhooks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: newWebhookUrl, events: newWebhookEvents }),
      });
      if (res.ok) {
        setNewWebhookUrl('');
        setNewWebhookEvents([]);
        showSuccess('Webhook created');
        fetchTabData('webhooks');
      } else {
        setError('Failed to create webhook');
      }
    } catch { setError('Failed to create webhook'); }
    finally { setSaving(false); }
  };

  const handleCreateExperiment = async () => {
    if (!newExpName.trim() || !newExpModelA.trim() || !newExpModelB.trim()) return;
    setSaving(true);
    try {
      const res = await fetch('/api/v1/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newExpName, model_a: newExpModelA, model_b: newExpModelB, description: newExpDesc }),
      });
      if (res.ok) {
        setNewExpName('');
        setNewExpModelA('');
        setNewExpModelB('');
        setNewExpDesc('');
        showSuccess('Experiment created');
        fetchTabData('experiments');
      } else {
        setError('Failed to create experiment');
      }
    } catch { setError('Failed to create experiment'); }
    finally { setSaving(false); }
  };

  const handleCreateRule = async () => {
    if (!newRuleName.trim() || !newRuleModel.trim()) return;
    setSaving(true);
    try {
      const res = await fetch('/api/v1/routing-rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newRuleName,
          preferred_model: newRuleModel,
          domain: newRuleDomain || undefined,
          min_complexity: newRuleMinComplexity ? parseFloat(newRuleMinComplexity) : undefined,
          max_complexity: newRuleMaxComplexity ? parseFloat(newRuleMaxComplexity) : undefined,
        }),
      });
      if (res.ok) {
        setNewRuleName('');
        setNewRuleModel('');
        setNewRuleDomain('');
        setNewRuleMinComplexity('');
        setNewRuleMaxComplexity('');
        showSuccess('Routing rule created');
        fetchTabData('routing');
      } else {
        setError('Failed to create routing rule');
      }
    } catch { setError('Failed to create routing rule'); }
    finally { setSaving(false); }
  };

  const toggleWebhookEvent = (event: string) => {
    setNewWebhookEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  if (needsAuth) {
    return (
      <div className="min-h-screen bg-gray-950 pt-14">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Settings className="w-7 h-7 text-cyan-400" />
            Settings
          </h1>
          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-8 text-center">
            <Key className="w-12 h-12 text-cyan-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Connect API Key to Manage Settings</h2>
            <p className="text-gray-400 mb-6 max-w-md mx-auto">
              Settings management requires authentication. Generate an API key from the Billing page to configure organizations, webhooks, experiments, and routing rules.
            </p>
            <a
              href="/billing"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm font-medium text-white transition-colors"
            >
              <Key className="w-4 h-4" />
              Go to Billing
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 pt-14">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
          <Settings className="w-7 h-7 text-cyan-400" />
          Settings
        </h1>

        {success && (
          <div className="mb-4 bg-green-900/30 border border-green-600 rounded-lg p-3 flex items-center gap-2 text-green-300 text-sm">
            <CheckCircle2 className="w-4 h-4" />
            {success}
          </div>
        )}
        {error && (
          <div className="mb-4 bg-red-900/30 border border-red-600 rounded-lg p-3 flex items-center gap-2 text-red-300 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200 text-xs">Dismiss</button>
          </div>
        )}

        <div className="flex gap-1 mb-6 border-b border-gray-800">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.key
                  ? 'text-cyan-400 border-cyan-400'
                  : 'text-gray-400 border-transparent hover:text-gray-200'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading...
          </div>
        ) : (
          <>
            {activeTab === 'organizations' && (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Create Organization</h3>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      placeholder="Organization name"
                      value={newOrgName}
                      onChange={(e) => setNewOrgName(e.target.value)}
                      className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      onClick={handleCreateOrg}
                      disabled={saving || !newOrgName.trim()}
                      className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                    >
                      {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      Create
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  {orgs.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Building2 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No organizations yet</p>
                    </div>
                  ) : (
                    orgs.map((org) => (
                      <div key={org.id} className="bg-gray-900/60 border border-gray-800 rounded-lg p-4 flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{org.name}</p>
                          <p className="text-xs text-gray-500 mt-1">{new Date(org.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'webhooks' && (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Create Webhook</h3>
                  <div className="space-y-4">
                    <input
                      type="url"
                      placeholder="Webhook URL (https://...)"
                      value={newWebhookUrl}
                      onChange={(e) => setNewWebhookUrl(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                    />
                    <div>
                      <p className="text-sm text-gray-400 mb-2">Events</p>
                      <div className="flex flex-wrap gap-2">
                        {WEBHOOK_EVENTS.map((event) => (
                          <button
                            key={event}
                            onClick={() => toggleWebhookEvent(event)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                              newWebhookEvents.includes(event)
                                ? 'bg-cyan-900/30 border-cyan-600 text-cyan-300'
                                : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                            }`}
                          >
                            {event}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button
                      onClick={handleCreateWebhook}
                      disabled={saving || !newWebhookUrl.trim()}
                      className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                    >
                      {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      Create Webhook
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  {webhooks.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Webhook className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No webhooks configured</p>
                    </div>
                  ) : (
                    webhooks.map((wh) => (
                      <div key={wh.id} className="bg-gray-900/60 border border-gray-800 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <code className="text-sm text-white font-mono">{wh.url}</code>
                          <span className={`w-2 h-2 rounded-full ${wh.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {wh.events.map((ev) => (
                            <span key={ev} className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
                              {ev}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'experiments' && (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Create Experiment</h3>
                  <div className="space-y-3">
                    <input
                      type="text"
                      placeholder="Experiment name"
                      value={newExpName}
                      onChange={(e) => setNewExpName(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                    />
                    <div className="grid grid-cols-2 gap-3">
                      <input
                        type="text"
                        placeholder="Model A"
                        value={newExpModelA}
                        onChange={(e) => setNewExpModelA(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      />
                      <input
                        type="text"
                        placeholder="Model B"
                        value={newExpModelB}
                        onChange={(e) => setNewExpModelB(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <textarea
                      placeholder="Description (optional)"
                      value={newExpDesc}
                      onChange={(e) => setNewExpDesc(e.target.value)}
                      rows={2}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 resize-none"
                    />
                    <button
                      onClick={handleCreateExperiment}
                      disabled={saving || !newExpName.trim() || !newExpModelA.trim() || !newExpModelB.trim()}
                      className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                    >
                      {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      Create Experiment
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  {experiments.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <FlaskConical className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No experiments yet</p>
                    </div>
                  ) : (
                    experiments.map((exp) => (
                      <div key={exp.id} className="bg-gray-900/60 border border-gray-800 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-white font-medium">{exp.name}</p>
                          <span className={`text-xs px-2 py-0.5 rounded border ${STATUS_COLORS[exp.status] || STATUS_COLORS.draft}`}>
                            {exp.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-400">
                          <span className="font-mono text-xs">{exp.model_a}</span>
                          <span className="text-gray-600">vs</span>
                          <span className="font-mono text-xs">{exp.model_b}</span>
                        </div>
                        {exp.description && (
                          <p className="text-xs text-gray-500 mt-2">{exp.description}</p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'routing' && (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Create Routing Rule</h3>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <input
                        type="text"
                        placeholder="Rule name"
                        value={newRuleName}
                        onChange={(e) => setNewRuleName(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      />
                      <input
                        type="text"
                        placeholder="Preferred model"
                        value={newRuleModel}
                        onChange={(e) => setNewRuleModel(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <input
                        type="text"
                        placeholder="Domain (e.g. biology)"
                        value={newRuleDomain}
                        onChange={(e) => setNewRuleDomain(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      />
                      <input
                        type="number"
                        placeholder="Min complexity"
                        value={newRuleMinComplexity}
                        onChange={(e) => setNewRuleMinComplexity(e.target.value)}
                        step="0.1"
                        min="0"
                        max="1"
                        className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      />
                      <input
                        type="number"
                        placeholder="Max complexity"
                        value={newRuleMaxComplexity}
                        onChange={(e) => setNewRuleMaxComplexity(e.target.value)}
                        step="0.1"
                        min="0"
                        max="1"
                        className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <button
                      onClick={handleCreateRule}
                      disabled={saving || !newRuleName.trim() || !newRuleModel.trim()}
                      className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                    >
                      {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      Create Rule
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  {rules.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Route className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No routing rules configured</p>
                    </div>
                  ) : (
                    rules.map((rule) => (
                      <div key={rule.id} className="bg-gray-900/60 border border-gray-800 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-white font-medium">{rule.name}</p>
                          <span className="text-xs font-mono text-cyan-400">{rule.preferred_model}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          {rule.domain && (
                            <span className="px-2 py-0.5 rounded bg-gray-800 border border-gray-700">{rule.domain}</span>
                          )}
                          {(rule.min_complexity !== undefined || rule.max_complexity !== undefined) && (
                            <span>
                              Complexity: {rule.min_complexity ?? 0} - {rule.max_complexity ?? 1}
                            </span>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
