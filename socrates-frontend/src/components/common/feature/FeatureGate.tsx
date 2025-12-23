/**
 * FeatureGate Component - Feature flag component
 */

import React from 'react';
import { Lock } from 'lucide-react';

interface FeatureGateProps {
  isEnabled: boolean;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requiredTier?: 'pro' | 'enterprise';
}

export const FeatureGate: React.FC<FeatureGateProps> = ({
  isEnabled,
  children,
  fallback,
  requiredTier,
}) => {
  if (!isEnabled) {
    return fallback ? (
      <>{fallback}</>
    ) : (
      <div className="p-6 bg-gray-50 dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 text-center">
        <Lock size={32} className="mx-auto text-gray-400 mb-3" />
        <p className="text-gray-700 dark:text-gray-300 font-medium">
          This feature is not available on your plan
        </p>
        {requiredTier && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Upgrade to {requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)} to unlock
          </p>
        )}
      </div>
    );
  }

  return <>{children}</>;
};

FeatureGate.displayName = 'FeatureGate';
