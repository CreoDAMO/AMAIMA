import React from 'react';

interface Props { 
  decision: {
    complexity: string;
    model: string;
    execution_mode: string;
    confidence: {
      complexity: number;
      model_fit: number;
      execution_fit: number;
      overall: number;
    };
    reasons: {
      complexity_reason: Array<{ label: string; code: string }>;
      model_reason: Array<{ label: string; code: string }>;
      execution_reason: Array<{ label: string; code: string }>;
    };
  };
}

export const RoutingExplanation = ({ decision }: Props) => {
  if (!decision) return null;

  return (
    <details className="mt-4 bg-gray-800 p-4 rounded-md border border-gray-700">
      <summary className="cursor-pointer text-blue-400 font-medium list-none flex items-center">
        <span className="mr-2">▶</span> Why this routing?
      </summary>
      <div className="mt-2 text-sm text-gray-300 space-y-3">
        <div>
          <p className="font-semibold text-blue-300">Complexity</p>
          <p>{decision.complexity} (Confidence: {(decision.confidence.complexity * 100).toFixed(1)}%)</p>
          <div className="flex flex-wrap mt-1">
            {decision.reasons.complexity_reason.map((r) => (
              <span key={r.code} className="bg-blue-900 text-blue-100 text-xs px-2 py-1 rounded mr-1 mb-1">
                {r.label}
              </span>
            ))}
          </div>
        </div>
        
        <div>
          <p className="font-semibold text-purple-300">Model Fit</p>
          <p>{decision.model} (Confidence: {(decision.confidence.model_fit * 100).toFixed(1)}%)</p>
          <div className="flex flex-wrap mt-1">
            {decision.reasons.model_reason.map((r) => (
              <span key={r.code} className="bg-purple-900 text-purple-100 text-xs px-2 py-1 rounded mr-1 mb-1">
                {r.label}
              </span>
            ))}
          </div>
        </div>

        <div>
          <p className="font-semibold text-green-300">Execution Mode</p>
          <p>{decision.execution_mode} (Confidence: {(decision.confidence.execution_fit * 100).toFixed(1)}%)</p>
          <div className="flex flex-wrap mt-1">
            {decision.reasons.execution_reason.map((r) => (
              <span key={r.code} className="bg-green-900 text-green-100 text-xs px-2 py-1 rounded mr-1 mb-1">
                {r.label}
              </span>
            ))}
          </div>
        </div>

        <div className="pt-2 border-t border-gray-700">
          <p><strong>Overall Confidence:</strong> {(decision.confidence.overall * 100).toFixed(1)}%</p>
          <p className="text-xs text-gray-500 italic mt-1">Weights: Complexity 0.4, Model 0.35, Execution 0.25</p>
        </div>

        <div className="mt-4 flex items-center space-x-4">
          <span className="text-xs text-gray-400 uppercase font-bold">Feedback:</span>
          <div className="flex space-x-2">
            <button className="hover:scale-110 transition-transform text-lg" title="Correct">👍</button>
            <button className="hover:scale-110 transition-transform text-lg" title="Neutral">😐</button>
            <button className="hover:scale-110 transition-transform text-lg" title="Incorrect">👎</button>
          </div>
        </div>
      </div>
    </details>
  );
};
