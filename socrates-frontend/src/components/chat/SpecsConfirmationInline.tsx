import React, { useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';

interface ExtractedSpecs {
  goals?: string[];
  requirements?: string[];
  tech_stack?: string[];
  constraints?: string[];
}

interface SpecsConfirmationInlineProps {
  specs: ExtractedSpecs;
  onConfirm: (specs: ExtractedSpecs) => Promise<void>;
  onDecline: () => void;
}

export const SpecsConfirmationInline: React.FC<SpecsConfirmationInlineProps> = ({
  specs,
  onConfirm,
  onDecline,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm(specs);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDecline = () => {
    onDecline();
  };

  const specsCount = (
    (specs.goals?.length || 0) +
    (specs.requirements?.length || 0) +
    (specs.tech_stack?.length || 0) +
    (specs.constraints?.length || 0)
  );

  return (
    <div className="mx-4 mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
      <div className="space-y-3">
        {/* Header */}
        <div>
          <p className="font-semibold text-slate-800 dark:text-slate-100">
            {specsCount} specification{specsCount !== 1 ? 's' : ''} detected
          </p>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
            Would you like to save these to your project?
          </p>
        </div>

        {/* Specs list */}
        {specsCount > 0 && (
          <div className="space-y-2 bg-white dark:bg-slate-800 p-3 rounded border border-blue-100 dark:border-blue-800/50 max-h-48 overflow-y-auto">
            {Array.isArray(specs.goals) && specs.goals.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wide">
                  Goals
                </p>
                <ul className="space-y-0.5">
                  {specs.goals.map((goal, idx) => (
                    <li key={idx} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-0.5">•</span>
                      <span>{goal}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(specs.requirements) && specs.requirements.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wide">
                  Requirements
                </p>
                <ul className="space-y-0.5">
                  {specs.requirements.map((req, idx) => (
                    <li key={idx} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-0.5">•</span>
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(specs.tech_stack) && specs.tech_stack.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wide">
                  Tech Stack
                </p>
                <ul className="space-y-0.5">
                  {specs.tech_stack.map((tech, idx) => (
                    <li key={idx} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-0.5">•</span>
                      <span>{tech}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(specs.constraints) && specs.constraints.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wide">
                  Constraints
                </p>
                <ul className="space-y-0.5">
                  {specs.constraints.map((constraint, idx) => (
                    <li key={idx} className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-0.5">•</span>
                      <span>{constraint}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle className="w-4 h-4" />
            {isLoading ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={handleDecline}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XCircle className="w-4 h-4" />
            Skip
          </button>
        </div>
      </div>
    </div>
  );
};
