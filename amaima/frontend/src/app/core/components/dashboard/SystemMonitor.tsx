'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/core/components/ui/card';
import { Badge } from '@/app/core/components/ui/badge';
import { useWebSocket } from '@/app/core/lib/websocket/WebSocketProvider';
import { cn } from '@/app/core/lib/utils/cn';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { Activity, Cpu, HardDrive, Zap, Server, Database } from 'lucide-react';
import { motion } from 'framer-motion';
import { formatRelativeTime } from '@/app/core/lib/utils/format';

interface SystemMetrics {
  timestamp: number;
  cpuUsage: number;
  memoryUsage: number;
  activeQueries: number;
  queriesPerMinute: number;
}

export function SystemMonitor() {
  const [metrics, setMetrics] = useState<SystemMetrics[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<SystemMetrics | null>(null);
  const { lastMessage, isConnected, connectionQuality } = useWebSocket();

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'system_status') return;

    const newMetric: SystemMetrics = {
      timestamp: Date.now(),
      cpuUsage: lastMessage.data.cpuUsage,
      memoryUsage: lastMessage.data.memoryUsage,
      activeQueries: lastMessage.data.activeQueries,
      queriesPerMinute: lastMessage.data.queriesPerMinute,
    };

    setCurrentMetrics(newMetric);
    setMetrics((prev) => [...prev.slice(-59), newMetric]);
  }, [lastMessage]);

  const StatCard = ({
    icon: Icon,
    title,
    value,
    unit = '',
    color,
    change,
  }: {
    icon: any;
    title: string;
    value: number;
    unit?: string;
    color: string;
    change?: string;
  }) => (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">
              {value.toFixed(1)}
              <span className="text-lg font-normal text-muted-foreground ml-1">
                {unit}
              </span>
            </p>
            {change && (
              <p
                className={cn(
                  'text-sm mt-1',
                  change.startsWith('+')
                    ? 'text-emerald-400'
                    : change.startsWith('-')
                    ? 'text-red-400'
                    : 'text-muted-foreground'
                )}
              >
                {change}
              </p>
            )}
          </div>
          <div
            className="p-3 rounded-xl"
            style={{ background: `${color}20` }}
          >
            <Icon className="h-6 w-6" style={{ color }} />
          </div>
        </div>

        {/* Mini Sparkline */}
        <div className="h-1 mt-4 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: color }}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(value, 100)}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </CardContent>
    </Card>
  );

  const getQualityColor = (quality: string) => {
    const colors: Record<string, string> = {
      excellent: 'text-emerald-400',
      good: 'text-cyan-400',
      poor: 'text-amber-400',
      disconnected: 'text-red-400',
    };
    return colors[quality] || 'text-gray-400';
  };

  if (!isConnected) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground animate-pulse" />
            <p className="text-muted-foreground">Connecting to system monitor...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'h-2 w-2 rounded-full',
                isConnected
                  ? 'bg-emerald-400 animate-pulse'
                  : 'bg-red-400'
              )}
            />
            <span className="text-sm font-medium">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <Badge variant="glass" className={getQualityColor(connectionQuality)}>
            {connectionQuality} connection
          </Badge>
        </div>
        {currentMetrics && (
          <span className="text-xs text-muted-foreground">
            Last updated: {formatRelativeTime(new Date(currentMetrics.timestamp))}
          </span>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Cpu}
          title="CPU Usage"
          value={currentMetrics?.cpuUsage || 0}
          unit="%"
          color="#22d3ee"
          change="+5.2%"
        />
        <StatCard
          icon={HardDrive}
          title="Memory Usage"
          value={currentMetrics?.memoryUsage || 0}
          unit="%"
          color="#a855f7"
          change="-2.1%"
        />
        <StatCard
          icon={Activity}
          title="Active Queries"
          value={currentMetrics?.activeQueries || 0}
          color="#ec4899"
        />
        <StatCard
          icon={Zap}
          title="Queries/Min"
          value={currentMetrics?.queriesPerMinute || 0}
          color="#10b981"
          change="+12.3%"
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* CPU & Memory */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Resource Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={metrics}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts) =>
                    new Date(ts).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  }
                  stroke="#6b7280"
                  fontSize={12}
                />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(0,0,0,0.8)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                  }}
                  labelFormatter={(ts) => new Date(ts).toLocaleString()}
                />
                <Area
                  type="monotone"
                  dataKey="cpuUsage"
                  stroke="#22d3ee"
                  fill="url(#cpuGradient)"
                  strokeWidth={2}
                  name="CPU %"
                />
                <Area
                  type="monotone"
                  dataKey="memoryUsage"
                  stroke="#a855f7"
                  fill="url(#memoryGradient)"
                  strokeWidth={2}
                  name="Memory %"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Query Throughput */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Query Throughput</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts) =>
                    new Date(ts).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  }
                  stroke="#6b7280"
                  fontSize={12}
                />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(0,0,0,0.8)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="queriesPerMinute"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  name="QPM"
                />
                <Line
                  type="monotone"
                  dataKey="activeQueries"
                  stroke="#ec4899"
                  strokeWidth={2}
                  dot={false}
                  name="Active"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
