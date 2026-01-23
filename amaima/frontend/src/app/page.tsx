'use client';

import { useState } from 'react';
import { Brain, Zap, Shield, Globe, Sparkles, Send, Loader2 } from 'lucide-react';

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState<string | null>(null);

  const features = [
    {
      icon: Brain,
      title: 'Intelligent Routing',
      description: 'Automatic model selection based on query complexity',
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-400/20',
    },
    {
      icon: Zap,
      title: 'Real-time Streaming',
      description: 'Instant responses with WebSocket streaming',
      color: 'text-purple-400',
      bgColor: 'bg-purple-400/20',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Enterprise-grade security with encrypted storage',
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-400/20',
    },
    {
      icon: Globe,
      title: 'Multi-Platform',
      description: 'Web, mobile, and API access anywhere',
      color: 'text-pink-400',
      bgColor: 'bg-pink-400/20',
    },
  ];

  const handleSubmit = async () => {
    if (!query.trim()) return;
    
    setIsSubmitting(true);
    setResponse(null);
    
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setResponse(`AMAIMA Response: Your query "${query.slice(0, 50)}${query.length > 50 ? '...' : ''}" has been analyzed. This is a demo response showcasing the AMAIMA interface.`);
    setIsSubmitting(false);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <section className="relative py-20 px-6 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] 
            bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full blur-3xl" />
        </div>

        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-white/20 bg-white/10 text-white text-xs font-semibold mb-4">
              <Sparkles className="h-3 w-3" />
              Next-Generation AI Platform
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-cyan-200 to-purple-200 
                bg-clip-text text-transparent">
                AMAIMA
              </span>
            </h1>
            
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Advanced Model-Aware Artificial Intelligence Management Interface. 
              Experience the future of intelligent query processing with adaptive model routing.
            </p>
          </div>

          <div className="mb-20">
            <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-xl overflow-hidden">
              <div className="p-6 border-b border-white/10">
                <h2 className="flex items-center gap-2 text-xl font-semibold text-white">
                  <Sparkles className="h-5 w-5 text-cyan-400" />
                  New Query
                </h2>
              </div>
              <div className="p-6 space-y-4">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Describe what you want to accomplish..."
                  className="w-full min-h-[150px] resize-none text-base bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                  disabled={isSubmitting}
                />

                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-slate-400 text-sm">Ready</span>
                  </div>

                  <button
                    onClick={handleSubmit}
                    disabled={!query.trim() || isSubmitting}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {isSubmitting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    Submit Query
                  </button>
                </div>

                {response && (
                  <div className="mt-4 p-4 rounded-lg bg-white/5 border border-white/10">
                    <p className="text-white">{response}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
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
            <Brain className="h-6 w-6 text-cyan-400" />
            <h2 className="text-2xl font-bold text-white">System Status</h2>
          </div>
          
          <div className="grid gap-4 md:grid-cols-4">
            {[
              { label: 'API Status', value: 'Online', color: 'text-emerald-400' },
              { label: 'Models Loaded', value: '5/5', color: 'text-cyan-400' },
              { label: 'Response Time', value: '~150ms', color: 'text-purple-400' },
              { label: 'Uptime', value: '99.9%', color: 'text-pink-400' },
            ].map((stat, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-4">
                <p className="text-sm text-slate-400">{stat.label}</p>
                <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="py-8 px-6 border-t border-white/5">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-cyan-400" />
              <span className="font-semibold text-white">AMAIMA</span>
            </div>
            <p className="text-sm text-slate-400">
              © 2025 AMAIMA. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
