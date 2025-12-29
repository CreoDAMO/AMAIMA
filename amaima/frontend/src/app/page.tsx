import { Suspense } from 'react';
import { QueryInput } from '@/components/query/QueryInput';
import { SystemMonitor } from '@/components/dashboard/SystemMonitor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, Zap, Shield, Globe, ArrowRight, Sparkles } from 'lucide-react';

export default function HomePage() {
  const features = [
    {
      icon: Brain,
      title: 'Intelligent Routing',
      description: 'Automatic model selection based on query complexity',
      color: 'text-cyan-400',
    },
    {
      icon: Zap,
      title: 'Real-time Streaming',
      description: 'Instant responses with WebSocket streaming',
      color: 'text-purple-400',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Enterprise-grade security with encrypted storage',
      color: 'text-emerald-400',
    },
    {
      icon: Globe,
      title: 'Multi-Platform',
      description: 'Web, mobile, and API access anywhere',
      color: 'text-pink-400',
    },
  ];

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 px-6 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] 
            bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full blur-3xl" />
        </div>

        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <Badge variant="glass" className="mb-4">
              <Sparkles className="h-3 w-3 mr-1" />
              Next-Generation AI Platform
            </Badge>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              <span className="bg-gradient-to-r from-white via-cyan-200 to-purple-200 
                bg-clip-text text-transparent">
                AMAIMA
              </span>
            </h1>
            
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Advanced Model-Aware Artificial Intelligence Management Interface. 
              Experience the future of intelligent query processing with adaptive model routing.
            </p>
          </div>

          {/* Query Input */}
          <div className="mb-20">
            <QueryInput />
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="group hover:scale-105 transition-all duration-300">
                <CardContent className="p-6">
                  <div
                    className={`p-3 rounded-xl inline-block mb-4 group-hover:scale-110 transition-transform`}
                    style={{ background: `${feature.color}20` }}
                  >
                    <feature.icon className={`h-6 w-6 ${feature.color}`} />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* System Status Section */}
      <section className="py-12 px-6 border-t border-white/5">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center gap-3 mb-8">
            <Brain className="h-6 w-6 text-cyan-400" />
            <h2 className="text-2xl font-bold">System Status</h2>
          </div>
          
          <Suspense fallback={<div className="h-96 bg-white/5 rounded-xl animate-pulse" />}>
            <SystemMonitor />
          </Suspense>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/5">
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-cyan-400" />
              <span className="font-semibold">AMAIMA</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 AMAIMA. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
