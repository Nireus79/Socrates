/**
 * ConflictResolutionModal - Modal for handling specification conflicts
 * Provides 4 resolution options based on CLI implementation:
 * 1. Keep existing specification
 * 2. Replace with new specification
 * 3. Skip this specification
 * 4. Manual resolution (edit both)
 */

import React from 'react';
import { X, AlertTriangle, Lightbulb, ChevronRight } from 'lucide-react';
import { Button, Card } from '../common';

interface Conflict {
  conflict_id: string;
  conflict_type: string;
  old_value: string;
  new_value: string;
  old_author: string;
  new_author: string;
  severity: string;
  suggestions: string[];
}

interface ConflictResolutionModalProps {
  conflicts: Conflict[];
  isOpen: boolean;
  onResolve: (resolution: any) => Promise<void>;
  onClose: () => void;
  isLoading?: boolean;
}

export const ConflictResolutionModal: React.FC<ConflictResolutionModalProps> = ({
  conflicts,
  isOpen,
  onResolve,
  onClose,
  isLoading = false,
}) => {
  const [currentConflictIndex, setCurrentConflictIndex] = React.useState(0);
  const [resolutions, setResolutions] = React.useState<{ [key: string]: string }>({});
  const [manualValue, setManualValue] = React.useState('');
  const [selectedOption, setSelectedOption] = React.useState<string | null>(null);

  if (!isOpen || conflicts.length === 0) {
    return null;
  }

  const currentConflict = conflicts[currentConflictIndex];
  const isLastConflict = currentConflictIndex === conflicts.length - 1;

  const handleResolution = async (choice: string) => {
    let resolvedValue = choice;
    if (choice === '4') {
      if (!manualValue.trim()) {
        return;
      }
      resolvedValue = manualValue;
    }

    const newResolutions = {
      ...resolutions,
      [currentConflict.conflict_id]: resolvedValue,
    };
    setResolutions(newResolutions);

    if (isLastConflict) {
      // All conflicts resolved
      try {
        await onResolve(newResolutions);
      } catch (error) {
        console.error('Failed to resolve conflicts:', error);
      }
    } else {
      // Move to next conflict
      setCurrentConflictIndex(currentConflictIndex + 1);
      setManualValue('');
      setSelectedOption(null);
    }
  };

  const handleManualInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setManualValue(e.target.value);
  };

  const getSeverityBadgeColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getSeverityIcon = (severity: string) => {
    if (severity === 'high') return 'High';
    if (severity === 'medium') return 'Medium';
    return 'Low';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col bg-white rounded-xl shadow-2xl">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-50 to-red-50 border-b border-orange-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-orange-600" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Specification Conflict Detected</h2>
              <p className="text-sm text-gray-600 mt-1">
                Resolving {currentConflictIndex + 1} of {conflicts.length}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Conflict Type and Severity */}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 capitalize">
              {currentConflict.conflict_type.replace(/_/g, ' ')}
            </h3>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getSeverityBadgeColor(currentConflict.severity)}`}>
              {getSeverityIcon(currentConflict.severity)} Severity
            </span>
          </div>

          {/* Conflict Values Comparison */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-2">
                Current Value
              </div>
              <div className="text-xs text-red-600 mb-2">by {currentConflict.old_author}</div>
              <div className="bg-white border border-red-100 rounded p-3 font-mono text-sm text-gray-900 break-words">
                {currentConflict.old_value}
              </div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">
                Proposed Value
              </div>
              <div className="text-xs text-green-600 mb-2">by {currentConflict.new_author}</div>
              <div className="bg-white border border-green-100 rounded p-3 font-mono text-sm text-gray-900 break-words">
                {currentConflict.new_value}
              </div>
            </div>
          </div>

          {/* Suggestions if available */}
          {currentConflict.suggestions && currentConflict.suggestions.length > 0 && (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-blue-900 mb-2">AI Suggestions</h4>
                  <ul className="space-y-2">
                    {currentConflict.suggestions.map((suggestion, index) => (
                      <li key={index} className="text-sm text-blue-800 flex gap-2">
                        <span className="text-blue-600 font-bold">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Resolution Options */}
          <div className="space-y-3 pt-2">
            <h4 className="text-sm font-semibold text-gray-900">How would you like to resolve this?</h4>

            <button
              onClick={() => {
                setSelectedOption('1');
                handleResolution('1');
              }}
              disabled={isLoading}
              className={`w-full text-left p-4 border-2 rounded-lg transition ${
                selectedOption === '1'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-gray-900">Keep Current Value</div>
                  <p className="text-sm text-gray-600 mt-1">Use: {currentConflict.old_value}</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </button>

            <button
              onClick={() => {
                setSelectedOption('2');
                handleResolution('2');
              }}
              disabled={isLoading}
              className={`w-full text-left p-4 border-2 rounded-lg transition ${
                selectedOption === '2'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-gray-900">Use New Value</div>
                  <p className="text-sm text-gray-600 mt-1">Use: {currentConflict.new_value}</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </button>

            <button
              onClick={() => {
                setSelectedOption('3');
                handleResolution('3');
              }}
              disabled={isLoading}
              className={`w-full text-left p-4 border-2 rounded-lg transition ${
                selectedOption === '3'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-gray-900">Skip This Specification</div>
                  <p className="text-sm text-gray-600 mt-1">Continue without adding either value</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </button>

            <div className={`border-2 rounded-lg p-4 transition ${
              selectedOption === '4'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}>
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="resolution"
                  checked={selectedOption === '4'}
                  onChange={() => setSelectedOption('4')}
                  className="mt-1"
                />
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-900">Custom Value</div>
                  <p className="text-sm text-gray-600 mt-1">Enter your preferred value:</p>
                  <input
                    type="text"
                    value={manualValue}
                    onChange={handleManualInput}
                    placeholder="Type your custom value here..."
                    className="w-full mt-2 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 flex gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-white transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              if (selectedOption === '4' && !manualValue.trim()) {
                return;
              }
              if (selectedOption) {
                handleResolution(selectedOption);
              }
            }}
            disabled={isLoading || !selectedOption || (selectedOption === '4' && !manualValue.trim())}
            className="flex-1 px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Resolving...' : isLastConflict ? 'Complete' : 'Next Conflict'}
          </button>
        </div>
      </Card>
    </div>
  );
};
