'use client';

import { useState, useCallback, useRef, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  Panel,
  MarkerType,
  type Node,
  type Edge,
  type Connection,
  type NodeProps,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Link from 'next/link';
import {
  ChevronLeft,
  Play,
  Save,
  Trash2,
  Plus,
  Brain,
  FlaskConical,
  Bot,
  Eye,
  Cpu,
  Loader2,
  CheckCircle,
  AlertCircle,
  Workflow,
  GitBranch,
  Search,
  Sparkles,
} from 'lucide-react';

const NODE_CATEGORIES = {
  agents: {
    label: 'Agent Nodes',
    icon: Brain,
    items: [
      { type: 'researcher', label: 'Researcher', icon: Search, color: '#3b82f6', model: 'meta/llama-3.1-70b-instruct' },
      { type: 'analyst', label: 'Analyst', icon: Cpu, color: '#8b5cf6', model: 'meta/llama-3.1-70b-instruct' },
      { type: 'synthesizer', label: 'Synthesizer', icon: Sparkles, color: '#06b6d4', model: 'meta/llama-3.1-8b-instruct' },
    ],
  },
  biology: {
    label: 'Biology',
    icon: FlaskConical,
    items: [
      { type: 'molecule_generator', label: 'Molecule Generator', icon: FlaskConical, color: '#10b981', model: 'nvidia/bionemo-megamolbart' },
      { type: 'admet_predictor', label: 'ADMET Predictor', icon: FlaskConical, color: '#22c55e', model: 'nvidia/bionemo-megamolbart' },
      { type: 'lead_optimizer', label: 'Lead Optimizer', icon: FlaskConical, color: '#14b8a6', model: 'meta/llama-3.1-70b-instruct' },
      { type: 'safety_reviewer', label: 'Safety Reviewer', icon: FlaskConical, color: '#059669', model: 'meta/llama-3.1-8b-instruct' },
    ],
  },
  robotics: {
    label: 'Robotics',
    icon: Bot,
    items: [
      { type: 'perception', label: 'Perception', icon: Eye, color: '#f59e0b', model: 'nvidia/cosmos-reason2-7b' },
      { type: 'path_planner', label: 'Path Planner', icon: GitBranch, color: '#f97316', model: 'nvidia/isaac-gr00t-n1.6' },
      { type: 'action_executor', label: 'Action Executor', icon: Bot, color: '#ef4444', model: 'meta/llama-3.1-8b-instruct' },
      { type: 'safety_monitor', label: 'Safety Monitor', icon: AlertCircle, color: '#dc2626', model: 'meta/llama-3.1-8b-instruct' },
    ],
  },
  workflow: {
    label: 'Workflow',
    icon: Workflow,
    items: [
      { type: 'condition', label: 'Condition', icon: GitBranch, color: '#a855f7', model: '' },
      { type: 'validator', label: 'Validator', icon: CheckCircle, color: '#6366f1', model: 'meta/llama-3.1-8b-instruct' },
    ],
  },
};

function AgentNode({ data, selected }: NodeProps) {
  const nodeColor = data.color as string || '#3b82f6';

  return (
    <div
      className={`px-4 py-3 rounded-xl border-2 min-w-[180px] shadow-lg transition-all ${
        selected ? 'ring-2 ring-white/50 scale-105' : ''
      }`}
      style={{
        background: `linear-gradient(135deg, ${nodeColor}20, ${nodeColor}10)`,
        borderColor: nodeColor,
      }}
    >
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-gray-400 !border-2 !border-gray-600" />
      <div className="flex items-center gap-2 mb-1">
        <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ backgroundColor: nodeColor }}>
          <Brain className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="text-sm font-semibold text-white">{data.label as string}</span>
      </div>
      {data.model ? (
        <p className="text-[10px] text-gray-400 truncate">{String(data.model)}</p>
      ) : null}
      {data.systemPrompt ? (
        <p className="text-[10px] text-gray-500 mt-1 truncate max-w-[160px]">{String(data.systemPrompt)}</p>
      ) : null}
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-gray-400 !border-2 !border-gray-600" />
    </div>
  );
}

function ConditionNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`px-4 py-3 rounded-xl border-2 min-w-[160px] shadow-lg ${
        selected ? 'ring-2 ring-white/50 scale-105' : ''
      }`}
      style={{
        background: 'linear-gradient(135deg, #a855f720, #a855f710)',
        borderColor: '#a855f7',
      }}
    >
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-gray-400 !border-2 !border-gray-600" />
      <div className="flex items-center gap-2 mb-1">
        <GitBranch className="w-4 h-4 text-purple-400" />
        <span className="text-sm font-semibold text-white">{data.label as string}</span>
      </div>
      <p className="text-[10px] text-gray-400">{(data.conditionDescription as string) || 'Conditional branch'}</p>
      <Handle type="source" position={Position.Bottom} id="true" className="!w-3 !h-3 !bg-green-400 !border-2 !border-green-600 !left-[30%]" />
      <Handle type="source" position={Position.Bottom} id="false" className="!w-3 !h-3 !bg-red-400 !border-2 !border-red-600 !left-[70%]" />
    </div>
  );
}

const nodeTypes = {
  agent: AgentNode,
  condition: ConditionNode,
};

const TEMPLATES = [
  {
    name: 'Research Pipeline',
    nodes: [
      { id: 'r1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Researcher', color: '#3b82f6', model: 'meta/llama-3.1-70b-instruct', systemPrompt: 'Research the topic thoroughly' } },
      { id: 'r2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Analyst', color: '#8b5cf6', model: 'meta/llama-3.1-70b-instruct', systemPrompt: 'Analyze research findings' } },
      { id: 'r3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Synthesizer', color: '#06b6d4', model: 'meta/llama-3.1-8b-instruct', systemPrompt: 'Synthesize a final report' } },
    ],
    edges: [
      { id: 'e1-2', source: 'r1', target: 'r2', animated: true },
      { id: 'e2-3', source: 'r2', target: 'r3', animated: true },
    ],
  },
  {
    name: 'Drug Discovery',
    nodes: [
      { id: 'd1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Molecule Generator', color: '#10b981', model: 'nvidia/bionemo-megamolbart', systemPrompt: 'Generate candidate molecules' } },
      { id: 'd2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'ADMET Predictor', color: '#22c55e', model: 'nvidia/bionemo-megamolbart', systemPrompt: 'Predict ADMET properties' } },
      { id: 'd3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Lead Optimizer', color: '#14b8a6', model: 'meta/llama-3.1-70b-instruct', systemPrompt: 'Optimize lead compounds' } },
      { id: 'd4', type: 'agent', position: { x: 250, y: 500 }, data: { label: 'Safety Reviewer', color: '#059669', model: 'meta/llama-3.1-8b-instruct', systemPrompt: 'Review safety profile' } },
    ],
    edges: [
      { id: 'e1-2', source: 'd1', target: 'd2', animated: true },
      { id: 'e2-3', source: 'd2', target: 'd3', animated: true },
      { id: 'e3-4', source: 'd3', target: 'd4', animated: true },
    ],
  },
  {
    name: 'Navigation Crew',
    nodes: [
      { id: 'n1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Perception', color: '#f59e0b', model: 'nvidia/cosmos-reason2-7b', systemPrompt: 'Analyze environment' } },
      { id: 'n2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Path Planner', color: '#f97316', model: 'nvidia/isaac-gr00t-n1.6', systemPrompt: 'Plan collision-free path' } },
      { id: 'n3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Action Executor', color: '#ef4444', model: 'meta/llama-3.1-8b-instruct', systemPrompt: 'Execute planned actions' } },
      { id: 'n4', type: 'agent', position: { x: 250, y: 500 }, data: { label: 'Safety Monitor', color: '#dc2626', model: 'meta/llama-3.1-8b-instruct', systemPrompt: 'Monitor safety constraints' } },
    ],
    edges: [
      { id: 'e1-2', source: 'n1', target: 'n2', animated: true },
      { id: 'e2-3', source: 'n2', target: 'n3', animated: true },
      { id: 'e3-4', source: 'n3', target: 'n4', animated: true },
    ],
  },
];

export default function AgentBuilderPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [taskInput, setTaskInput] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>('agents');
  const nodeIdCounter = useRef(1);

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds: Edge[]) =>
        addEdge(
          {
            ...connection,
            animated: true,
          },
          eds
        )
      );
    },
    [setEdges]
  );

  const addNode = useCallback(
    (item: any) => {
      const id = `node_${nodeIdCounter.current++}`;
      const isCondition = item.type === 'condition';
      const newNode: Node = {
        id,
        type: isCondition ? 'condition' : 'agent',
        position: { x: 250 + Math.random() * 100, y: 100 + nodes.length * 120 },
        data: {
          label: item.label,
          color: item.color,
          model: item.model,
          systemPrompt: '',
          ...(isCondition ? { conditionDescription: 'Check quality threshold' } : {}),
        },
      };
      setNodes((nds: Node[]) => [...nds, newNode]);
    },
    [nodes.length, setNodes]
  );

  const loadTemplate = useCallback(
    (template: typeof TEMPLATES[0]) => {
      setNodes(template.nodes as Node[]);
      setEdges(template.edges as Edge[]);
      setResult(null);
      setError(null);
    },
    [setNodes, setEdges]
  );

  const clearCanvas = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setResult(null);
    setError(null);
  }, [setNodes, setEdges]);

  const runWorkflow = useCallback(async () => {
    if (!taskInput.trim() || nodes.length === 0) {
      setError('Please add agent nodes and enter a task description');
      return;
    }

    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const roles = nodes
        .filter((n) => n.type === 'agent')
        .map((n) => ({
          name: n.data.label as string,
          goal: (n.data.systemPrompt as string) || `Handle ${n.data.label} tasks`,
          backstory: `Expert ${n.data.label} agent powered by ${n.data.model || 'NIM'}`,
          model: n.data.model as string,
        }));

      const res = await fetch('/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crew_type: 'custom',
          task: taskInput,
          roles,
          process: 'sequential',
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setResult(data);
      } else {
        setError(data.detail || 'Failed to run workflow');
      }
    } catch (err: any) {
      setError(err.message || 'Network error');
    } finally {
      setRunning(false);
    }
  }, [taskInput, nodes]);

  const defaultEdgeOptions = useMemo(
    () => ({
      style: { stroke: '#6b7280', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed as const, color: '#6b7280' },
    }),
    []
  );

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-white">
      <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-xl z-50 px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <ChevronLeft className="w-4 h-4" />
            <span className="text-sm">Dashboard</span>
          </Link>
          <div className="h-5 w-px bg-gray-700" />
          <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Agent Builder
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearCanvas}
            className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg flex items-center gap-1.5 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
          <button
            onClick={runWorkflow}
            disabled={running || nodes.length === 0}
            className="px-4 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 rounded-lg flex items-center gap-1.5 font-medium transition-colors"
          >
            {running ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            {running ? 'Running...' : 'Run Workflow'}
          </button>
        </div>
      </nav>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 border-r border-gray-800 bg-gray-900/50 flex flex-col overflow-y-auto flex-shrink-0">
          <div className="p-3 border-b border-gray-800">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Templates</p>
            <div className="space-y-1">
              {TEMPLATES.map((t) => (
                <button
                  key={t.name}
                  onClick={() => loadTemplate(t)}
                  className="w-full text-left px-3 py-2 text-xs rounded-lg bg-gray-800/50 hover:bg-gray-800 border border-gray-700/50 hover:border-gray-600 transition-colors"
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 flex-1">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Drag to Add</p>
            {Object.entries(NODE_CATEGORIES).map(([key, cat]) => {
              const CatIcon = cat.icon;
              const isExpanded = expandedCategory === key;
              return (
                <div key={key} className="mb-2">
                  <button
                    onClick={() => setExpandedCategory(isExpanded ? null : key)}
                    className="w-full flex items-center gap-2 px-2 py-1.5 text-xs font-medium text-gray-300 hover:text-white rounded transition-colors"
                  >
                    <CatIcon className="w-3.5 h-3.5" />
                    {cat.label}
                  </button>
                  {isExpanded && (
                    <div className="ml-2 space-y-1 mt-1">
                      {cat.items.map((item) => (
                        <button
                          key={item.type}
                          onClick={() => addNode(item)}
                          className="w-full text-left px-3 py-2 text-xs rounded-lg border border-gray-700/50 hover:border-gray-600 transition-all flex items-center gap-2 group"
                          style={{ backgroundColor: `${item.color}10` }}
                        >
                          <Plus className="w-3 h-3 text-gray-500 group-hover:text-white transition-colors" />
                          <span className="text-gray-300 group-hover:text-white">{item.label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="p-3 border-t border-gray-800">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">
              Task Description
            </label>
            <textarea
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder="Describe the task for the agent crew..."
              rows={4}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>
        </aside>

        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            fitView
            className="bg-gray-950"
            colorMode="dark"
          >
            <Controls className="!bg-gray-800 !border-gray-700 !rounded-lg [&>button]:!bg-gray-800 [&>button]:!border-gray-700 [&>button]:!text-gray-400 [&>button:hover]:!bg-gray-700" />
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#374151" />

            {nodes.length === 0 && (
              <Panel position="top-center">
                <div className="mt-32 text-center">
                  <Workflow className="w-16 h-16 mx-auto mb-4 text-gray-600" />
                  <h2 className="text-xl font-semibold text-gray-400 mb-2">Build Your Agent Workflow</h2>
                  <p className="text-sm text-gray-500 max-w-md">
                    Click agent nodes from the sidebar or load a template to get started.
                    Connect nodes by dragging from one handle to another.
                  </p>
                </div>
              </Panel>
            )}
          </ReactFlow>

          {(result || error) && (
            <div className="absolute bottom-4 right-4 w-96 max-h-80 overflow-y-auto bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  {error ? (
                    <>
                      <AlertCircle className="w-4 h-4 text-red-400" />
                      <span className="text-red-400">Error</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-green-400">Result</span>
                    </>
                  )}
                </h3>
                <button
                  onClick={() => { setResult(null); setError(null); }}
                  className="text-xs text-gray-500 hover:text-gray-300"
                >
                  Dismiss
                </button>
              </div>
              {error ? (
                <p className="text-xs text-red-300">{error}</p>
              ) : result ? (
                <div className="space-y-2">
                  <p className="text-xs text-gray-400">
                    Crew: {result.crew} | Process: {result.process} | Latency: {result.total_latency_ms}ms
                  </p>
                  {result.results?.map((r: any, i: number) => (
                    <div key={i} className="bg-gray-800 rounded-lg p-2">
                      <p className="text-[10px] font-medium text-blue-400">{r.agent}</p>
                      <p className="text-xs text-gray-300 mt-1 line-clamp-3">{r.response || r.error}</p>
                    </div>
                  ))}
                  {result.final_output && (
                    <div className="bg-green-900/20 border border-green-800 rounded-lg p-2 mt-2">
                      <p className="text-[10px] font-medium text-green-400">Final Output</p>
                      <p className="text-xs text-gray-300 mt-1">{result.final_output}</p>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
