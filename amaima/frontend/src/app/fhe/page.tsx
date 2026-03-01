'use client';

import { useState, useEffect, useCallback } from 'react';
import { Brain, Shield, Zap, Lock, Activity, ShieldCheck, Microscope, Search, Vote, BarChart3, Calculator } from 'lucide-react';
import Link from 'next/link';

interface FHEStatus {
  subsystem: string;
  version: string;
  cryptographic_backend: string;
  lattice_basis: string;
  post_quantum_secure: boolean;
  security_level_bits: number;
  supported_schemes: Record<string, any>;
  supported_operations: string[];
  high_level_services: string[];
  engine_stats: Record<string, any>;
}

interface DemoResult {
  demo_name: string;
  description: string;
  cryptographic_foundation: Record<string, any>;
  demos: Record<string, any>;
  total_latency_ms: number;
  engine_stats: Record<string, any>;
}

export default function FHEPage() {
  const [status, setStatus] = useState<FHEStatus | null>(null);
  const [demoResult, setDemoResult] = useState<DemoResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  const [customResult, setCustomResult] = useState<any>(null);
  const [customLoading, setCustomLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/fhe/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch FHE status:', err);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const runDemo = async () => {
    setDemoLoading(true);
    try {
      const res = await fetch('/api/v1/fhe/demo');
      if (res.ok) {
        const data = await res.json();
        setDemoResult(data);
      }
    } catch (err) {
      console.error('Failed to run FHE demo:', err);
    } finally {
      setDemoLoading(false);
    }
  };

  const runCustomDemo = async (type: string) => {
    setCustomLoading(true);
    setActiveDemo(type);
    try {
      let endpoint = '';
      let body: any = {};

      switch (type) {
        case 'drug-scoring':
          endpoint = '/api/v1/fhe/drug-scoring';
          body = {
            qed_values: [0.85, 0.72, 0.93, 0.61, 0.78],
            plogp_values: [0.42, 0.68, 0.35, 0.74, 0.55],
          };
          break;
        case 'similarity-search':
          endpoint = '/api/v1/fhe/similarity-search';
          body = {
            query_embedding: [0.2, 0.6, 0.1, 0.9, 0.4],
            candidate_embeddings: [
              [0.3, 0.5, 0.2, 0.8, 0.3],
              [0.8, 0.1, 0.7, 0.2, 0.9],
              [0.25, 0.55, 0.15, 0.88, 0.38],
              [0.1, 0.9, 0.3, 0.4, 0.6],
            ],
          };
          break;
        case 'secure-vote':
          endpoint = '/api/v1/fhe/secure-vote';
          body = { votes: [0, 1, 2, 0, 1, 0, 2, 1, 0, 0, 1, 2, 0, 1, 0], num_candidates: 3 };
          break;
        case 'secure-aggregation':
          endpoint = '/api/v1/fhe/secure-aggregation';
          body = {
            datasets: [
              [100, 200, 300, 400],
              [110, 190, 310, 390],
              [95, 205, 295, 410],
              [105, 195, 305, 395],
            ],
          };
          break;
        case 'vector-arithmetic':
          endpoint = '/api/v1/fhe/vector-arithmetic';
          body = {
            vector_a: [3.14, 2.71, 1.41, 1.73],
            vector_b: [1.0, 2.0, 3.0, 4.0],
            operations: ['add', 'multiply', 'dot_product', 'negate_a'],
            scheme: 'CKKS',
          };
          break;
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const data = await res.json();
        setCustomResult(data);
      }
    } catch (err) {
      console.error('Custom demo error:', err);
    } finally {
      setCustomLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <Link href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <Brain className="w-5 h-5" />
            <span className="font-medium">Dashboard</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/agent-builder" className="text-gray-400 hover:text-white text-sm font-medium transition-colors">
              Agent Builder
            </Link>
            <div className="h-4 w-px bg-gray-800" />
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
              <Shield className="w-4 h-4" />
              FHE Secured
            </div>
          </div>
        </div>

        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full px-4 py-1.5 mb-4">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            <span className="text-emerald-300 text-sm font-medium">Post-Quantum Secure</span>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent mb-3">
            Fully Homomorphic Encryption v4
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Beyond Latency: Error Tracking, Energy Profiling, and Verifiable Computation.
            Post-Quantum RLWE Security.
          </p>
        </div>

        {status && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Backend</div>
              <div className="text-lg font-semibold text-emerald-400">Microsoft SEAL</div>
              <div className="text-xs text-gray-500 mt-1">via TenSEAL</div>
            </div>
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Lattice Basis</div>
              <div className="text-lg font-semibold text-cyan-400">RLWE</div>
              <div className="text-xs text-gray-500 mt-1">Ring Learning With Errors</div>
            </div>
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Security Level</div>
              <div className="text-lg font-semibold text-blue-400">{status.security_level_bits}-bit</div>
              <div className="text-xs text-gray-500 mt-1">Post-quantum resistant</div>
            </div>
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Operations</div>
              <div className="text-lg font-semibold text-purple-400">
                {status.engine_stats.homomorphic_ops || 0}
              </div>
              <div className="text-xs text-gray-500 mt-1">Homomorphic ops performed</div>
            </div>
          </div>
        )}

        {status && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {Object.entries(status.supported_schemes).map(([name, scheme]: [string, any]) => (
              <div key={name} className="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-3 h-3 rounded-full ${name === 'CKKS' ? 'bg-cyan-400' : 'bg-purple-400'}`} />
                  <h3 className="text-xl font-bold">{name}</h3>
                  <span className="text-xs bg-gray-800 px-2 py-0.5 rounded-full text-gray-400">
                    {name === 'CKKS' ? 'Real Numbers' : 'Integers'}
                  </span>
                </div>
                <p className="text-gray-400 text-sm mb-3">{scheme.description}</p>
                <div className="flex flex-wrap gap-2">
                  {scheme.use_cases.map((uc: string) => (
                    <span key={uc} className="text-xs bg-gray-800/80 border border-gray-700 px-2 py-1 rounded-md text-gray-300">
                      {uc}
                    </span>
                  ))}
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  Polynomial degrees: {scheme.poly_modulus_degrees?.join(', ') || 'N/A'}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">Live FHE Demonstrations</h2>
              <p className="text-gray-400 text-sm mt-1">
                Real homomorphic encryption operations on actual RLWE lattice ciphertexts
              </p>
            </div>
            <button
              onClick={runDemo}
              disabled={demoLoading}
              className="px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 rounded-lg font-medium transition-all disabled:opacity-50"
            >
              {demoLoading ? 'Running All Demos...' : 'Run All Demos'}
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            {[
              { id: 'drug-scoring', label: 'Drug Scoring', icon: '🧬', color: 'from-green-600 to-emerald-600' },
              { id: 'similarity-search', label: 'Similarity Search', icon: '🔍', color: 'from-blue-600 to-cyan-600' },
              { id: 'secure-vote', label: 'Secure Voting', icon: '🗳️', color: 'from-purple-600 to-violet-600' },
              { id: 'secure-aggregation', label: 'Aggregation', icon: '📊', color: 'from-orange-600 to-amber-600' },
              { id: 'vector-arithmetic', label: 'Vector Math', icon: '🔢', color: 'from-pink-600 to-rose-600' },
            ].map((demo) => (
              <button
                key={demo.id}
                onClick={() => runCustomDemo(demo.id)}
                disabled={customLoading}
                className={`px-4 py-3 bg-gradient-to-r ${demo.color} hover:opacity-90 rounded-lg text-sm font-medium transition-all disabled:opacity-50 text-center`}
              >
                <div className="text-lg mb-1">{demo.icon}</div>
                {demo.label}
              </button>
            ))}
          </div>

          {customResult && activeDemo && (
            <div className="bg-gray-950/50 border border-gray-700 rounded-lg p-5 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <h3 className="text-lg font-semibold text-emerald-400">
                  {customResult.operation || activeDemo}
                </h3>
                <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full">
                  {customResult.scheme}
                </span>
                <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">
                  {customResult.total_latency_ms}ms
                </span>
                {customResult.energy_nj && (
                  <span className="text-xs bg-orange-500/20 text-orange-300 px-2 py-0.5 rounded-full">
                    {customResult.energy_nj.toFixed(2)} nJ
                  </span>
                )}
                {customResult.proof_id && (
                  <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full">
                    Proof: {customResult.proof_id.substring(0, 8)}...
                  </span>
                )}
              </div>

              {customResult.composite_scores && (
                <div className="space-y-2">
                  <div className="text-sm text-gray-400">Encrypted Drug Composite Scores:</div>
                  <div className="flex gap-2 flex-wrap">
                    {customResult.composite_scores.map((s: number, i: number) => (
                      <div key={i} className="flex flex-col gap-1">
                        <div className={`px-3 py-1.5 rounded-md text-sm font-mono ${i === customResult.best_molecule_index ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300' : 'bg-gray-800 text-gray-300'}`}>
                          Mol {i}: {s.toFixed(4)}
                          {i === customResult.best_molecule_index && ' ★'}
                        </div>
                        {customResult.error_bounds && (
                          <div className="text-[10px] text-gray-500 px-1">
                            err: {customResult.error_bounds[i]?.toExponential(2)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {customResult.tallies && (
                <div className="space-y-2">
                  <div className="text-sm text-gray-400">Encrypted Vote Tallies ({customResult.total_voters} voters):</div>
                  <div className="flex gap-3">
                    {Object.entries(customResult.tallies).map(([k, v]: [string, any]) => (
                      <div key={k} className={`px-4 py-2 rounded-md text-sm ${k === customResult.winner ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300' : 'bg-gray-800 text-gray-300'}`}>
                        {k}: {v} {k === customResult.winner && '(Winner)'}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {customResult.results && customResult.candidates_searched && (
                <div className="space-y-2">
                  <div className="text-sm text-gray-400">Encrypted Similarity Search ({customResult.candidates_searched} candidates):</div>
                  <div className="space-y-1">
                    {customResult.results.map((r: any, i: number) => (
                      <div key={i} className={`flex items-center gap-3 px-3 py-1.5 rounded-md text-sm ${i === 0 ? 'bg-blue-500/20 border border-blue-500/40 text-blue-300' : 'bg-gray-800 text-gray-300'}`}>
                        <span className="font-mono">Candidate {r.candidate_index}</span>
                        <div className="flex-1 bg-gray-700 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${Math.min(r.similarity_score * 100, 100)}%` }} />
                        </div>
                        <span className="font-mono">{r.similarity_score.toFixed(6)}</span>
                        {i === 0 && <span className="text-blue-400">Best</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {customResult.aggregated_mean && (
                <div className="space-y-2">
                  <div className="text-sm text-gray-400">Encrypted Secure Aggregation ({customResult.num_participants} participants):</div>
                  <div className="flex gap-2 flex-wrap">
                    {customResult.aggregated_mean.map((v: number, i: number) => (
                      <div key={i} className="px-3 py-1.5 bg-orange-500/20 border border-orange-500/30 rounded-md text-sm font-mono text-orange-300">
                        dim[{i}]: {v.toFixed(4)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {customResult.encrypted_results && (
                <div className="space-y-3">
                  <div className="text-sm text-gray-400">Encrypted vs Plaintext Verification:</div>
                  {Object.entries(customResult.encrypted_results).map(([op, val]: [string, any]) => (
                    <div key={op} className="grid grid-cols-3 gap-3 text-sm">
                      <div className="bg-gray-800 px-3 py-1.5 rounded-md font-medium text-pink-300">{op}</div>
                      <div className="bg-gray-800 px-3 py-1.5 rounded-md font-mono text-gray-300">
                        FHE: {Array.isArray(val) ? val.map((v: number) => v.toFixed(4)).join(', ') : typeof val === 'number' ? val.toFixed(6) : (val?.toString() || 'N/A')}
                      </div>
                      <div className="bg-gray-800 px-3 py-1.5 rounded-md font-mono text-emerald-300">
                        Plain: {(() => {
                          const pv = customResult.plaintext_verification?.[op];
                          if (pv === undefined || pv === null) return 'N/A';
                          return Array.isArray(pv) ? pv.map((v: number) => v.toFixed(4)).join(', ') : typeof pv === 'number' ? pv.toFixed(6) : pv.toString();
                        })()}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-4 p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-md">
                <div className="text-xs text-emerald-400 font-medium mb-1">Privacy Guarantee</div>
                <div className="text-xs text-gray-400">{customResult.privacy_guarantee}</div>
              </div>
            </div>
          )}
        </div>

        {demoResult && (
          <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-xl font-bold">Comprehensive Demo Results</h2>
              <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full">
                {demoResult.total_latency_ms}ms total
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              {demoResult.cryptographic_foundation.key_properties.map((prop: string, i: number) => (
                <div key={i} className="bg-gray-950/50 border border-gray-700 rounded-md p-3">
                  <div className="text-xs text-emerald-400">{prop}</div>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              {Object.entries(demoResult.demos).map(([name, demo]: [string, any]) => (
                <div key={name} className="bg-gray-950/50 border border-gray-700 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-semibold text-white">{demo.operation}</span>
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">{demo.scheme}</span>
                    <span className="text-xs text-gray-500">{demo.total_latency_ms}ms</span>
                  </div>
                  <pre className="text-xs text-gray-400 bg-gray-950 rounded p-3 overflow-x-auto max-h-40">
                    {JSON.stringify(
                      Object.fromEntries(
                        Object.entries(demo).filter(([k]) =>
                          ['encrypted_results', 'plaintext_verification', 'composite_scores', 'tallies', 'winner', 'results', 'aggregated_mean'].includes(k)
                        )
                      ),
                      null,
                      2
                    )}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-bold mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center text-emerald-400 font-bold">1</div>
              <h3 className="font-semibold">Key Generation</h3>
              <p className="text-sm text-gray-400">
                Generate RLWE lattice-based public/secret key pairs. The security relies on the hardness of
                the Ring Learning With Errors problem, believed resistant to quantum computers.
              </p>
            </div>
            <div className="space-y-3">
              <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center text-cyan-400 font-bold">2</div>
              <h3 className="font-semibold">Encrypted Computation</h3>
              <p className="text-sm text-gray-400">
                Data is encrypted into lattice ciphertexts. Homomorphic operations (add, multiply, dot product)
                are performed directly on ciphertexts using RLWE-based evaluation.
              </p>
            </div>
            <div className="space-y-3">
              <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center text-blue-400 font-bold">3</div>
              <h3 className="font-semibold">Secure Decryption</h3>
              <p className="text-sm text-gray-400">
                Only the key holder can decrypt results. The computation output is mathematically identical
                to operating on plaintext, but privacy is preserved throughout.
              </p>
            </div>
          </div>
        </div>

        {status && (
          <div className="mt-8 bg-gray-900/80 border border-gray-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4">API Reference</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-gray-800">
                    <th className="pb-2 pr-4">Endpoint</th>
                    <th className="pb-2 pr-4">Method</th>
                    <th className="pb-2">Description</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  {[
                    ['/v1/fhe/status', 'GET', 'FHE subsystem status and capabilities'],
                    ['/v1/fhe/keygen', 'POST', 'Generate RLWE key pair (BFV or CKKS)'],
                    ['/v1/fhe/encrypt', 'POST', 'Encrypt vector into lattice ciphertext'],
                    ['/v1/fhe/compute', 'POST', 'Homomorphic operations on ciphertexts'],
                    ['/v1/fhe/decrypt', 'POST', 'Decrypt ciphertext (key holder only)'],
                    ['/v1/fhe/drug-scoring', 'POST', 'Encrypted drug QED/plogP scoring'],
                    ['/v1/fhe/similarity-search', 'POST', 'Encrypted embedding similarity search'],
                    ['/v1/fhe/secure-vote', 'POST', 'Private ballot tallying (BFV)'],
                    ['/v1/fhe/secure-aggregation', 'POST', 'Multi-party encrypted mean'],
                    ['/v1/fhe/vector-arithmetic', 'POST', 'Encrypted vector math with verification'],
                    ['/v1/fhe/demo', 'GET', 'Run all demos with live results'],
                  ].map(([endpoint, method, desc]) => (
                    <tr key={endpoint} className="border-b border-gray-800/50">
                      <td className="py-2 pr-4 font-mono text-emerald-400">{endpoint}</td>
                      <td className="py-2 pr-4">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${method === 'GET' ? 'bg-blue-500/20 text-blue-300' : 'bg-green-500/20 text-green-300'}`}>
                          {method}
                        </span>
                      </td>
                      <td className="py-2 text-gray-400">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
