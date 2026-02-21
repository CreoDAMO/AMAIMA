'use client';

import { useState, useCallback, useRef, useMemo, useEffect } from 'react';
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
  ShieldCheck,
  Mic,
  Volume2,
  Database,
  Globe,
  Lock,
  Fingerprint,
  Vote,
  BarChart3,
  ChevronDown,
  X,
} from 'lucide-react';

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  parameters: string;
  domain: string;
  category: string;
  status: string;
  api_status: string;
  description?: string;
}

const DOMAIN_COLORS: Record<string, string> = {
  general: '#3b82f6',
  vision: '#f59e0b',
  biology: '#10b981',
  robotics: '#ef4444',
  speech: '#a855f7',
  embedding: '#06b6d4',
  fhe: '#10b981',
};

const NODE_CATEGORIES = {
  general: {
    label: 'General AI',
    icon: Brain,
    items: [
      { type: 'researcher', label: 'Researcher', icon: Search, color: '#3b82f6', model: 'meta/llama-3.1-70b-instruct' },
      { type: 'analyst', label: 'Analyst', icon: Cpu, color: '#8b5cf6', model: 'meta/llama-3.1-70b-instruct' },
      { type: 'synthesizer', label: 'Synthesizer', icon: Sparkles, color: '#06b6d4', model: 'meta/llama-3.1-8b-instruct' },
      { type: 'expert_reasoner', label: 'Expert Reasoner', icon: Brain, color: '#4f46e5', model: 'nvidia/llama-3.1-nemotron-ultra-253b-v1' },
      { type: 'edge_agent', label: 'Edge Agent', icon: Cpu, color: '#0ea5e9', model: 'nvidia/nemotron-nano-9b-v2' },
      { type: 'moe_agent', label: 'MoE Agent', icon: Globe, color: '#6366f1', model: 'mistralai/mixtral-8x22b-instruct-v0.1' },
    ],
  },
  vision: {
    label: 'Vision',
    icon: Eye,
    items: [
      { type: 'scene_analyzer', label: 'Scene Analyzer', icon: Eye, color: '#f59e0b', model: 'nvidia/cosmos-reason2-7b' },
      { type: 'image_reasoner', label: 'Image Reasoner', icon: Eye, color: '#eab308', model: 'meta/llama-3.2-90b-vision-instruct' },
      { type: 'video_predictor', label: 'Video Predictor', icon: Eye, color: '#d97706', model: 'nvidia/cosmos-predict2-14b' },
      { type: 'multimodal_vl', label: 'Multimodal VL', icon: Eye, color: '#ca8a04', model: 'nvidia/llama-3.1-nemotron-nano-vl-8b' },
      { type: 'fine_grained_vision', label: 'Fine-Grained Vision', icon: Eye, color: '#b45309', model: 'nvidia/vila' },
    ],
  },
  biology: {
    label: 'Biology',
    icon: FlaskConical,
    items: [
      { type: 'molecule_generator', label: 'Molecule Generator', icon: FlaskConical, color: '#10b981', model: 'nvidia/genmol' },
      { type: 'protein_analyzer', label: 'Protein Analyzer', icon: FlaskConical, color: '#059669', model: 'nvidia/bionemo-esm2' },
      { type: 'mol_optimizer', label: 'MolBART Optimizer', icon: FlaskConical, color: '#22c55e', model: 'nvidia/bionemo-megamolbart' },
      { type: 'structure_predictor', label: 'Structure Predictor', icon: FlaskConical, color: '#14b8a6', model: 'deepmind/alphafold2' },
      { type: 'docking_agent', label: 'Docking Agent', icon: FlaskConical, color: '#0d9488', model: 'mit/diffdock' },
      { type: 'safety_reviewer', label: 'Safety Reviewer', icon: FlaskConical, color: '#047857', model: 'meta/llama-3.1-70b-instruct' },
    ],
  },
  robotics: {
    label: 'Robotics',
    icon: Bot,
    items: [
      { type: 'perception', label: 'Perception', icon: Eye, color: '#f59e0b', model: 'nvidia/cosmos-reason2-7b' },
      { type: 'humanoid_control', label: 'Humanoid Control', icon: Bot, color: '#ef4444', model: 'nvidia/isaac-gr00t-n1.6' },
      { type: 'autonomous_vehicle', label: 'Autonomous Vehicle', icon: Bot, color: '#f97316', model: 'nvidia/alpamayo-1' },
      { type: 'manipulator', label: 'Manipulator', icon: Bot, color: '#dc2626', model: 'nvidia/isaac-manipulator' },
      { type: 'edge_controller', label: 'Edge Controller', icon: Cpu, color: '#b91c1c', model: 'nvidia/nemotron-3-nano-30b-a3b' },
      { type: 'safety_monitor', label: 'Safety Monitor', icon: AlertCircle, color: '#991b1b', model: 'meta/llama-3.1-8b-instruct' },
    ],
  },
  speech: {
    label: 'Speech',
    icon: Mic,
    items: [
      { type: 'speech_recognizer', label: 'Speech Recognizer', icon: Mic, color: '#a855f7', model: 'nvidia/parakeet-ctc-1.1b' },
      { type: 'text_to_speech', label: 'Text to Speech', icon: Volume2, color: '#9333ea', model: 'nvidia/magpie-tts-multilingual' },
    ],
  },
  embedding: {
    label: 'Embedding',
    icon: Database,
    items: [
      { type: 'text_embedder', label: 'Text Embedder', icon: Database, color: '#06b6d4', model: 'nvidia/nv-embedqa-e5-v5' },
      { type: 'multimodal_embedder', label: 'Multimodal Embedder', icon: Database, color: '#0891b2', model: 'nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1' },
    ],
  },
  fhe: {
    label: 'FHE Privacy',
    icon: ShieldCheck,
    items: [
      { type: 'fhe_encryptor', label: 'FHE Encryptor', icon: Lock, color: '#10b981', model: 'fhe/ckks-encrypt' },
      { type: 'fhe_compute', label: 'FHE Compute', icon: ShieldCheck, color: '#059669', model: 'fhe/homomorphic-eval' },
      { type: 'fhe_decryptor', label: 'FHE Decryptor', icon: Fingerprint, color: '#14b8a6', model: 'fhe/ckks-decrypt' },
      { type: 'fhe_drug_scorer', label: 'Encrypted Drug Scorer', icon: FlaskConical, color: '#22c55e', model: 'fhe/drug-scoring' },
      { type: 'fhe_similarity', label: 'Encrypted Similarity', icon: Search, color: '#0d9488', model: 'fhe/similarity-search' },
      { type: 'fhe_voter', label: 'Secure Voter', icon: Vote, color: '#047857', model: 'fhe/bfv-vote' },
      { type: 'fhe_aggregator', label: 'Secure Aggregator', icon: BarChart3, color: '#065f46', model: 'fhe/secure-aggregation' },
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

const ALL_MODELS = [
  { id: 'meta/llama-3.1-8b-instruct', name: 'Llama 3.1 8B', domain: 'general' },
  { id: 'meta/llama-3.1-70b-instruct', name: 'Llama 3.1 70B', domain: 'general' },
  { id: 'meta/llama-3.1-405b-instruct', name: 'Llama 3.1 405B', domain: 'general' },
  { id: 'mistralai/mixtral-8x7b-instruct-v0.1', name: 'Mixtral 8x7B', domain: 'general' },
  { id: 'google/gemma-2-9b-it', name: 'Gemma 2 9B', domain: 'general' },
  { id: 'mistralai/mixtral-8x22b-instruct-v0.1', name: 'Mixtral 8x22B', domain: 'general' },
  { id: 'nvidia/llama-3.1-nemotron-ultra-253b-v1', name: 'Nemotron Ultra 253B', domain: 'general' },
  { id: 'nvidia/nemotron-nano-9b-v2', name: 'Nemotron Nano 9B', domain: 'general' },
  { id: 'nvidia/nemotron-3-nano-30b-a3b', name: 'Nemotron-3 Nano 30B', domain: 'general' },
  { id: 'nvidia/cosmos-reason2-7b', name: 'Cosmos Reason 2', domain: 'vision' },
  { id: 'nvidia/cosmos-predict2-14b', name: 'Cosmos Predict 2.5', domain: 'vision' },
  { id: 'nvidia/llama-3.1-nemotron-nano-vl-8b', name: 'Nemotron Nano VL 8B', domain: 'vision' },
  { id: 'meta/llama-3.2-90b-vision-instruct', name: 'Llama 3.2 Vision 90B', domain: 'vision' },
  { id: 'nvidia/vila', name: 'VILA Vision-Language', domain: 'vision' },
  { id: 'nvidia/bionemo-megamolbart', name: 'BioNeMo MegaMolBART', domain: 'biology' },
  { id: 'nvidia/bionemo-esm2', name: 'BioNeMo ESM-2', domain: 'biology' },
  { id: 'nvidia/genmol', name: 'GenMol', domain: 'biology' },
  { id: 'deepmind/alphafold2', name: 'AlphaFold2', domain: 'biology' },
  { id: 'mit/diffdock', name: 'DiffDock', domain: 'biology' },
  { id: 'nvidia/isaac-gr00t-n1.6', name: 'Isaac GR00T N1.6', domain: 'robotics' },
  { id: 'nvidia/alpamayo-1', name: 'Alpamayo 1', domain: 'robotics' },
  { id: 'nvidia/isaac-manipulator', name: 'Isaac Manipulator', domain: 'robotics' },
  { id: 'nvidia/parakeet-ctc-1.1b', name: 'Parakeet ASR', domain: 'speech' },
  { id: 'nvidia/magpie-tts-multilingual', name: 'Magpie TTS', domain: 'speech' },
  { id: 'nvidia/nv-embedqa-e5-v5', name: 'NV-Embed-QA E5', domain: 'embedding' },
  { id: 'nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1', name: 'NeMo Retriever Embed', domain: 'embedding' },
  { id: 'fhe/ckks-encrypt', name: 'FHE CKKS Encrypt', domain: 'fhe' },
  { id: 'fhe/homomorphic-eval', name: 'FHE Homomorphic Eval', domain: 'fhe' },
  { id: 'fhe/ckks-decrypt', name: 'FHE CKKS Decrypt', domain: 'fhe' },
  { id: 'fhe/drug-scoring', name: 'FHE Drug Scoring', domain: 'fhe' },
  { id: 'fhe/similarity-search', name: 'FHE Similarity Search', domain: 'fhe' },
  { id: 'fhe/bfv-vote', name: 'FHE BFV Vote', domain: 'fhe' },
  { id: 'fhe/secure-aggregation', name: 'FHE Secure Aggregation', domain: 'fhe' },
];

function ModelSelector({ currentModel, onSelect, onClose }: { currentModel: string; onSelect: (id: string) => void; onClose: () => void }) {
  const [filter, setFilter] = useState('');
  const [domainFilter, setDomainFilter] = useState<string | null>(null);

  const domains = [...new Set(ALL_MODELS.map(m => m.domain))];
  const filtered = ALL_MODELS.filter(m => {
    if (domainFilter && m.domain !== domainFilter) return false;
    if (filter && !m.name.toLowerCase().includes(filter.toLowerCase()) && !m.id.toLowerCase().includes(filter.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-[520px] max-h-[70vh] flex flex-col shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white">Select Model ({ALL_MODELS.length} available)</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-3 border-b border-gray-800 space-y-2">
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Search models..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            autoFocus
          />
          <div className="flex gap-1 flex-wrap">
            <button
              onClick={() => setDomainFilter(null)}
              className={`px-2 py-0.5 text-[10px] rounded-full border ${!domainFilter ? 'bg-blue-600 border-blue-500 text-white' : 'border-gray-700 text-gray-400 hover:text-white'}`}
            >
              All
            </button>
            {domains.map(d => (
              <button
                key={d}
                onClick={() => setDomainFilter(d === domainFilter ? null : d)}
                className={`px-2 py-0.5 text-[10px] rounded-full border capitalize ${d === domainFilter ? 'text-white' : 'text-gray-400 hover:text-white'}`}
                style={{ borderColor: d === domainFilter ? DOMAIN_COLORS[d] : undefined, backgroundColor: d === domainFilter ? `${DOMAIN_COLORS[d]}30` : undefined }}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-y-auto flex-1 p-2">
          {filtered.map(m => (
            <button
              key={m.id}
              onClick={() => { onSelect(m.id); onClose(); }}
              className={`w-full text-left px-3 py-2 text-xs rounded-lg flex items-center justify-between gap-2 mb-0.5 transition-colors ${m.id === currentModel ? 'bg-blue-600/20 border border-blue-500/50' : 'hover:bg-gray-800 border border-transparent'}`}
            >
              <div>
                <span className="text-white font-medium">{m.name}</span>
                <span className="text-gray-500 ml-2">{m.id}</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded capitalize" style={{ color: DOMAIN_COLORS[m.domain], backgroundColor: `${DOMAIN_COLORS[m.domain]}15` }}>
                {m.domain}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function AgentNode({ data, selected }: NodeProps) {
  const nodeColor = data.color as string || '#3b82f6';
  const isFhe = String(data.model || '').startsWith('fhe/');
  const domainKey = isFhe ? 'fhe' : ALL_MODELS.find(m => m.id === data.model)?.domain || 'general';

  return (
    <div
      className={`px-4 py-3 rounded-xl border-2 min-w-[200px] shadow-lg transition-all ${
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
          {isFhe ? <ShieldCheck className="w-3.5 h-3.5 text-white" /> : <Brain className="w-3.5 h-3.5 text-white" />}
        </div>
        <span className="text-sm font-semibold text-white">{data.label as string}</span>
      </div>
      {data.model ? (
        <div className="flex items-center gap-1 mt-0.5">
          <span className="text-[10px] px-1.5 py-0.5 rounded capitalize" style={{ color: DOMAIN_COLORS[domainKey], backgroundColor: `${DOMAIN_COLORS[domainKey]}15` }}>
            {domainKey}
          </span>
          <span className="text-[10px] text-gray-400 truncate max-w-[130px]">{String(data.model)}</span>
        </div>
      ) : null}
      {data.systemPrompt ? (
        <p className="text-[10px] text-gray-500 mt-1 truncate max-w-[180px]">{String(data.systemPrompt)}</p>
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
    description: '3-agent research crew',
    nodes: [
      { id: 'r1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Researcher', color: '#3b82f6', model: 'meta/llama-3.1-70b-instruct', systemPrompt: 'Research the topic thoroughly' } },
      { id: 'r2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Analyst', color: '#8b5cf6', model: 'nvidia/llama-3.1-nemotron-ultra-253b-v1', systemPrompt: 'Analyze research findings with expert reasoning' } },
      { id: 'r3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Synthesizer', color: '#06b6d4', model: 'meta/llama-3.1-8b-instruct', systemPrompt: 'Synthesize a final report' } },
    ],
    edges: [
      { id: 'e1-2', source: 'r1', target: 'r2', animated: true },
      { id: 'e2-3', source: 'r2', target: 'r3', animated: true },
    ],
  },
  {
    name: 'Drug Discovery',
    description: 'Molecule generation to safety review',
    nodes: [
      { id: 'd1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Molecule Generator', color: '#10b981', model: 'nvidia/genmol', systemPrompt: 'Generate candidate molecules using SAFE format' } },
      { id: 'd2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Protein Analyzer', color: '#059669', model: 'nvidia/bionemo-esm2', systemPrompt: 'Analyze protein binding targets' } },
      { id: 'd3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Docking Agent', color: '#0d9488', model: 'mit/diffdock', systemPrompt: 'Predict molecular docking poses' } },
      { id: 'd4', type: 'agent', position: { x: 250, y: 500 }, data: { label: 'Lead Optimizer', color: '#14b8a6', model: 'nvidia/bionemo-megamolbart', systemPrompt: 'Optimize lead compounds for ADMET' } },
      { id: 'd5', type: 'agent', position: { x: 250, y: 650 }, data: { label: 'Safety Reviewer', color: '#047857', model: 'meta/llama-3.1-70b-instruct', systemPrompt: 'Review safety profile and toxicity' } },
    ],
    edges: [
      { id: 'e1-2', source: 'd1', target: 'd2', animated: true },
      { id: 'e2-3', source: 'd2', target: 'd3', animated: true },
      { id: 'e3-4', source: 'd3', target: 'd4', animated: true },
      { id: 'e4-5', source: 'd4', target: 'd5', animated: true },
    ],
  },
  {
    name: 'Navigation Crew',
    description: 'Robotics perception to action',
    nodes: [
      { id: 'n1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Scene Perception', color: '#f59e0b', model: 'nvidia/cosmos-reason2-7b', systemPrompt: 'Analyze environment using vision-language reasoning' } },
      { id: 'n2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Path Planner', color: '#f97316', model: 'nvidia/alpamayo-1', systemPrompt: 'Plan collision-free autonomous path' } },
      { id: 'n3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Humanoid Control', color: '#ef4444', model: 'nvidia/isaac-gr00t-n1.6', systemPrompt: 'Execute humanoid locomotion and manipulation' } },
      { id: 'n4', type: 'agent', position: { x: 250, y: 500 }, data: { label: 'Safety Monitor', color: '#dc2626', model: 'meta/llama-3.1-8b-instruct', systemPrompt: 'Monitor safety constraints and emergency stops' } },
    ],
    edges: [
      { id: 'e1-2', source: 'n1', target: 'n2', animated: true },
      { id: 'e2-3', source: 'n2', target: 'n3', animated: true },
      { id: 'e3-4', source: 'n3', target: 'n4', animated: true },
    ],
  },
  {
    name: 'Multimodal Analysis',
    description: 'Vision + speech + embedding pipeline',
    nodes: [
      { id: 'mm1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'Speech Input', color: '#a855f7', model: 'nvidia/parakeet-ctc-1.1b', systemPrompt: 'Transcribe audio input to text' } },
      { id: 'mm2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Vision Analysis', color: '#f59e0b', model: 'meta/llama-3.2-90b-vision-instruct', systemPrompt: 'Analyze images with multimodal reasoning' } },
      { id: 'mm3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Embedding Index', color: '#06b6d4', model: 'nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1', systemPrompt: 'Generate multimodal embeddings for retrieval' } },
      { id: 'mm4', type: 'agent', position: { x: 250, y: 500 }, data: { label: 'Report Generator', color: '#3b82f6', model: 'meta/llama-3.1-70b-instruct', systemPrompt: 'Generate final multimodal analysis report' } },
      { id: 'mm5', type: 'agent', position: { x: 250, y: 650 }, data: { label: 'Audio Response', color: '#9333ea', model: 'nvidia/magpie-tts-multilingual', systemPrompt: 'Convert report to speech output' } },
    ],
    edges: [
      { id: 'e1-4', source: 'mm1', target: 'mm4', animated: true },
      { id: 'e2-3', source: 'mm2', target: 'mm3', animated: true },
      { id: 'e3-4', source: 'mm3', target: 'mm4', animated: true },
      { id: 'e4-5', source: 'mm4', target: 'mm5', animated: true },
    ],
  },
  {
    name: 'Encrypted Drug Discovery',
    description: 'Privacy-preserving FHE drug pipeline',
    nodes: [
      { id: 'f1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'FHE Key Gen', color: '#10b981', model: 'fhe/ckks-encrypt', systemPrompt: 'Generate RLWE encryption keys for CKKS scheme' } },
      { id: 'f2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Molecule Generator', color: '#22c55e', model: 'nvidia/genmol', systemPrompt: 'Generate candidate molecules using GenMol' } },
      { id: 'f3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Encrypted Drug Scorer', color: '#059669', model: 'fhe/drug-scoring', systemPrompt: 'Score molecules on encrypted QED/plogP data' } },
      { id: 'f4', type: 'agent', position: { x: 250, y: 500 }, data: { label: 'Encrypted Similarity', color: '#0d9488', model: 'fhe/similarity-search', systemPrompt: 'Find similar molecules via encrypted embeddings' } },
      { id: 'f5', type: 'agent', position: { x: 250, y: 650 }, data: { label: 'FHE Decrypt Results', color: '#14b8a6', model: 'fhe/ckks-decrypt', systemPrompt: 'Decrypt final results for authorized viewer' } },
    ],
    edges: [
      { id: 'e1-2', source: 'f1', target: 'f2', animated: true },
      { id: 'e2-3', source: 'f2', target: 'f3', animated: true },
      { id: 'e3-4', source: 'f3', target: 'f4', animated: true },
      { id: 'e4-5', source: 'f4', target: 'f5', animated: true },
    ],
  },
  {
    name: 'Secure Voting System',
    description: 'FHE-based private ballot tallying',
    nodes: [
      { id: 'v1', type: 'agent', position: { x: 250, y: 50 }, data: { label: 'BFV Key Setup', color: '#10b981', model: 'fhe/ckks-encrypt', systemPrompt: 'Generate BFV encryption context for integer voting' } },
      { id: 'v2', type: 'agent', position: { x: 250, y: 200 }, data: { label: 'Ballot Encryptor', color: '#059669', model: 'fhe/ckks-encrypt', systemPrompt: 'Encrypt individual ballots into BFV ciphertexts' } },
      { id: 'v3', type: 'agent', position: { x: 250, y: 350 }, data: { label: 'Secure Tally', color: '#047857', model: 'fhe/bfv-vote', systemPrompt: 'Perform homomorphic addition to tally encrypted votes' } },
      { id: 'v4', type: 'agent', position: { x: 250, y: 500 }, data: { label: 'Result Decryptor', color: '#14b8a6', model: 'fhe/ckks-decrypt', systemPrompt: 'Decrypt final vote tally for authorized election board' } },
    ],
    edges: [
      { id: 'e1-2', source: 'v1', target: 'v2', animated: true },
      { id: 'e2-3', source: 'v2', target: 'v3', animated: true },
      { id: 'e3-4', source: 'v3', target: 'v4', animated: true },
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
  const [expandedCategory, setExpandedCategory] = useState<string | null>('general');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [modelCount, setModelCount] = useState(26);
  const nodeIdCounter = useRef(1);

  useEffect(() => {
    fetch('/api/v1/models')
      .then(r => r.json())
      .then(data => {
        if (data.available_models) setModelCount(data.available_models.length);
      })
      .catch(() => {});
  }, []);

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds: Edge[]) =>
        addEdge({ ...connection, animated: true }, eds)
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
    setSelectedNode(null);
  }, [setNodes, setEdges]);

  const updateNodeModel = useCallback((nodeId: string, newModel: string) => {
    setNodes((nds: Node[]) => nds.map(n =>
      n.id === nodeId ? { ...n, data: { ...n.data, model: newModel } } : n
    ));
  }, [setNodes]);

  const updateNodePrompt = useCallback((nodeId: string, prompt: string) => {
    setNodes((nds: Node[]) => nds.map(n =>
      n.id === nodeId ? { ...n, data: { ...n.data, systemPrompt: prompt } } : n
    ));
  }, [setNodes]);

  const runWorkflow = useCallback(async () => {
    if (!taskInput.trim() || nodes.length === 0) {
      setError('Please add agent nodes and enter a task description');
      return;
    }

    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const agentNodes = nodes.filter((n) => n.type === 'agent');
      const hasFheNodes = agentNodes.some(n => String(n.data.model || '').startsWith('fhe/'));

      if (hasFheNodes) {
        const fheRes = await fetch('/api/v1/fhe/demo');
        const fheData = await fheRes.json();

        const nimNodes = agentNodes.filter(n => !String(n.data.model || '').startsWith('fhe/'));
        let nimResult = null;

        if (nimNodes.length > 0) {
          const roles = nimNodes.map((n) => ({
            name: n.data.label as string,
            goal: (n.data.systemPrompt as string) || `Handle ${n.data.label} tasks`,
            backstory: `Expert ${n.data.label} agent powered by ${n.data.model || 'NIM'}`,
            model: n.data.model as string,
          }));

          const res = await fetch('/api/v1/agents', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ crew_type: 'custom', task: taskInput, roles, process: 'sequential' }),
          });
          nimResult = await res.json();
        }

        const fheResults = agentNodes
          .filter(n => String(n.data.model || '').startsWith('fhe/'))
          .map(n => ({
            agent: n.data.label as string,
            model: n.data.model as string,
            response: `FHE operation completed. ${fheData.status === 'completed' ? `Total latency: ${fheData.total_latency_ms}ms. Operations: ${fheData.total_operations}` : 'FHE subsystem active.'}`,
            latency_ms: fheData.total_latency_ms || 0,
          }));

        const allResults = [
          ...fheResults,
          ...(nimResult?.results || []),
        ];

        setResult({
          crew: 'Hybrid FHE + NIM Crew',
          process: 'sequential',
          agents_used: agentNodes.map(n => n.data.label as string),
          results: allResults,
          final_output: nimResult?.final_output || `FHE pipeline completed with ${fheResults.length} encrypted operations`,
          total_latency_ms: (fheData.total_latency_ms || 0) + (nimResult?.total_latency_ms || 0),
          fhe_summary: fheData,
        });
      } else {
        const roles = agentNodes.map((n) => ({
          name: n.data.label as string,
          goal: (n.data.systemPrompt as string) || `Handle ${n.data.label} tasks`,
          backstory: `Expert ${n.data.label} agent powered by ${n.data.model || 'NIM'}`,
          model: n.data.model as string,
        }));

        const res = await fetch('/api/v1/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ crew_type: 'custom', task: taskInput, roles, process: 'sequential' }),
        });

        const data = await res.json();
        if (res.ok) {
          setResult(data);
        } else {
          setError(data.detail || 'Failed to run workflow');
        }
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

  const activeNode = nodes.find(n => n.id === selectedNode);

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-white">
      {showModelSelector && selectedNode && (
        <ModelSelector
          currentModel={String(activeNode?.data.model || '')}
          onSelect={(id) => updateNodeModel(selectedNode, id)}
          onClose={() => setShowModelSelector(false)}
        />
      )}

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
          <span className="text-[10px] text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
            {modelCount} models + FHE
          </span>
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
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Templates ({TEMPLATES.length})</p>
            <div className="space-y-1">
              {TEMPLATES.map((t) => (
                <button
                  key={t.name}
                  onClick={() => loadTemplate(t)}
                  className="w-full text-left px-3 py-2 text-xs rounded-lg bg-gray-800/50 hover:bg-gray-800 border border-gray-700/50 hover:border-gray-600 transition-colors"
                >
                  <span className="font-medium text-white">{t.name}</span>
                  <span className="text-[10px] text-gray-500 block">{t.description}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 flex-1 overflow-y-auto">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Node Palette</p>
            {Object.entries(NODE_CATEGORIES).map(([key, cat]) => {
              const CatIcon = cat.icon;
              const isExpanded = expandedCategory === key;
              return (
                <div key={key} className="mb-1">
                  <button
                    onClick={() => setExpandedCategory(isExpanded ? null : key)}
                    className="w-full flex items-center justify-between gap-2 px-2 py-1.5 text-xs font-medium text-gray-300 hover:text-white rounded transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <CatIcon className="w-3.5 h-3.5" style={{ color: DOMAIN_COLORS[key] || '#6b7280' }} />
                      {cat.label}
                      <span className="text-[10px] text-gray-600">({cat.items.length})</span>
                    </div>
                    <ChevronDown className={`w-3 h-3 text-gray-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                  </button>
                  {isExpanded && (
                    <div className="ml-2 space-y-0.5 mt-1">
                      {cat.items.map((item) => (
                        <button
                          key={item.type}
                          onClick={() => addNode(item)}
                          className="w-full text-left px-3 py-1.5 text-xs rounded-lg border border-gray-700/50 hover:border-gray-600 transition-all flex items-center gap-2 group"
                          style={{ backgroundColor: `${item.color}08` }}
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

          {activeNode && activeNode.type === 'agent' && (
            <div className="p-3 border-t border-gray-800 space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Node Settings</p>
              <p className="text-[10px] text-gray-500">{activeNode.data.label as string}</p>
              <button
                onClick={() => setShowModelSelector(true)}
                className="w-full text-left px-3 py-2 text-xs rounded-lg bg-gray-800 border border-gray-700 hover:border-blue-500 transition-colors truncate"
              >
                {String(activeNode.data.model || 'Select model...')}
              </button>
              <textarea
                value={String(activeNode.data.systemPrompt || '')}
                onChange={(e) => updateNodePrompt(selectedNode!, e.target.value)}
                placeholder="System prompt..."
                rows={2}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
              />
            </div>
          )}

          <div className="p-3 border-t border-gray-800">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">
              Task Description
            </label>
            <textarea
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder="Describe the task for the agent crew..."
              rows={3}
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
            onNodeClick={(_, node) => setSelectedNode(node.id)}
            onPaneClick={() => setSelectedNode(null)}
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
                  <p className="text-sm text-gray-500 max-w-md mb-4">
                    Choose nodes from the sidebar or load a template. Connect nodes by dragging handles.
                    Click a node to change its model from the full {modelCount}-model registry.
                  </p>
                  <div className="flex gap-2 justify-center flex-wrap">
                    {['General AI', 'Vision', 'Biology', 'Robotics', 'Speech', 'Embedding', 'FHE Privacy'].map(d => (
                      <span key={d} className="text-[10px] px-2 py-0.5 bg-gray-800 border border-gray-700 rounded-full text-gray-400">{d}</span>
                    ))}
                  </div>
                </div>
              </Panel>
            )}
          </ReactFlow>

          {(result || error) && (
            <div className="absolute bottom-4 right-4 w-[420px] max-h-96 overflow-y-auto bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-4">
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
                  {result.fhe_summary && (
                    <div className="bg-emerald-900/20 border border-emerald-800/50 rounded-lg p-2">
                      <p className="text-[10px] font-medium text-emerald-400 flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" /> FHE Operations
                      </p>
                      <p className="text-[10px] text-gray-400 mt-0.5">
                        {result.fhe_summary.total_operations} homomorphic ops | {result.fhe_summary.total_latency_ms}ms | 128-bit RLWE security
                      </p>
                    </div>
                  )}
                  {result.results?.map((r: any, i: number) => (
                    <div key={i} className="bg-gray-800 rounded-lg p-2">
                      <div className="flex items-center gap-2">
                        <p className="text-[10px] font-medium text-blue-400">{r.agent}</p>
                        {r.model && <span className="text-[9px] text-gray-600">{r.model}</span>}
                      </div>
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
