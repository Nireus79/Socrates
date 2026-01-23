import React, { useState } from 'react';
import { Modal } from '../common/dialog/Modal';
import { Button } from '../common/interactive/Button';
import { CheckCircle, XCircle } from 'lucide-react';

interface ExtractedSpecs {
  goals?: string[];
  requirements?: string[];
  tech_stack?: string[];
  constraints?: string[];
}

interface SpecsConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  specs: ExtractedSpecs;
  onConfirm: (specs: ExtractedSpecs) => Promise<void>;
  onDecline: () => void;
}

export const SpecsConfirmationModal: React.FC<SpecsConfirmationModalProps> = ({
  isOpen,
  onClose,
  specs,
  onConfirm,
  onDecline,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm(specs);
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  const handleDecline = () => {
    onDecline();
    onClose();
  };

  // Count total specs
  const specsCount = (
    (specs.goals?.length || 0) +
    (specs.requirements?.length || 0) +
    (specs.tech_stack?.length || 0) +
    (specs.constraints?.length || 0)
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Save Detected Specifications"
      size="lg"
    >
      <div className="flex flex-col h-full">
        {/* Info message */}
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 flex-shrink-0">
          <div className="flex items-start gap-3">
            <div>
              <p className="font-semibold text-slate-800 dark:text-slate-100">
                {specsCount} specification{specsCount !== 1 ? 's' : ''} detected
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                Would you like to save these to your project?
              </p>
            </div>
          </div>
        </div>

        {/* Detected specs list - scrollable */}
        {specsCount > 0 && (
          <div className="overflow-y-auto flex-grow my-4 space-y-3 bg-slate-50 dark:bg-slate-900/30 p-4 rounded-lg">
            {Array.isArray(specs.goals) && specs.goals.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Goals
                </p>
                <ul className="space-y-1">
                  {specs.goals.map((goal, idx) => (
                    <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-1">•</span>
                      <span>{goal}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(specs.requirements) && specs.requirements.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Requirements
                </p>
                <ul className="space-y-1">
                  {specs.requirements.map((req, idx) => (
                    <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-1">•</span>
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(specs.tech_stack) && specs.tech_stack.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Tech Stack
                </p>
                <ul className="space-y-1">
                  {specs.tech_stack.map((tech, idx) => (
                    <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-1">•</span>
                      <span>{tech}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(specs.constraints) && specs.constraints.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Constraints
                </p>
                <ul className="space-y-1">
                  {specs.constraints.map((constraint, idx) => (
                    <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                      <span className="mt-1">•</span>
                      <span>{constraint}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons - Fixed at bottom */}
        <div className="flex gap-2 pt-4 border-t border-slate-200 dark:border-slate-700 flex-shrink-0">
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle className="w-4 h-4" />
            {isLoading ? 'Saving...' : 'Save Specifications'}
          </button>
          <button
            onClick={handleDecline}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XCircle className="w-4 h-4" />
            Skip for Now
          </button>
        </div>
      </div>
    </Modal>
  );
};
