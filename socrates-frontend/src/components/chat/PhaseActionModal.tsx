import React, { useState } from 'react';
import { Modal } from '../common/dialog/Modal';
import { Button } from '../common/interactive/Button';
import { ChevronRight, RotateCcw } from 'lucide-react';

interface PhaseActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPhase: string;
  nextPhase: string;
  onAdvance: () => Promise<void>;
  onEnrich: () => void;
}

export const PhaseActionModal: React.FC<PhaseActionModalProps> = ({
  isOpen,
  onClose,
  currentPhase,
  nextPhase,
  onAdvance,
  onEnrich,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleAdvance = async () => {
    setIsLoading(true);
    try {
      await onAdvance();
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnrich = () => {
    onEnrich();
    onClose();
  };

  const phaseNames: Record<string, string> = {
    discovery: 'Discovery',
    analysis: 'Analysis',
    design: 'Design',
    implementation: 'Implementation',
  };

  const currentPhaseName = phaseNames[currentPhase] || currentPhase;
  const nextPhaseName = phaseNames[nextPhase] || nextPhase;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Phase Complete" size="lg">
      <div className="space-y-6">
        {/* Completion message */}
        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-start gap-3">
            <div className="text-2xl">✨</div>
            <div>
              <p className="font-semibold text-slate-800 dark:text-slate-100">
                Excellent work on the {currentPhaseName} phase!
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                You've thoroughly explored the project specifications.
              </p>
            </div>
          </div>
        </div>

        {/* Options */}
        <div className="space-y-3">
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            What would you like to do?
          </p>

          {/* Advance Option */}
          <button
            onClick={handleAdvance}
            disabled={isLoading}
            className="w-full p-4 text-left rounded-lg border-2 border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <ChevronRight className="w-4 h-4" />
                  Advance to {nextPhaseName} Phase
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                  Move forward with implementing your ideas
                </p>
              </div>
            </div>
          </button>

          {/* Enrich Option */}
          <button
            onClick={handleEnrich}
            disabled={isLoading}
            className="w-full p-4 text-left rounded-lg border-2 border-slate-200 dark:border-slate-700 hover:border-amber-400 dark:hover:border-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <RotateCcw className="w-4 h-4" />
                  Enrich {currentPhaseName} Phase Further
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                  Deepen your understanding and fill in any remaining gaps
                </p>
              </div>
            </div>
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-700">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleAdvance}
            disabled={isLoading}
            {...(isLoading && { loading: true })}
          >
            {isLoading ? 'Advancing...' : `Advance to ${nextPhaseName}`}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
