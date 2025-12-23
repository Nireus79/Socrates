/**
 * SubscriptionRequired Component - Tier requirement message
 */

import React from 'react';
import { CreditCard } from 'lucide-react';

interface SubscriptionRequiredProps {
  requiredTier: 'pro' | 'enterprise';
  onUpgrade?: () => void;
  title?: string;
  description?: string;
}

export const SubscriptionRequired: React.FC<SubscriptionRequiredProps> = ({
  requiredTier,
  onUpgrade,
  title,
  description,
}) => {
  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 text-center">
      <CreditCard size={40} className="mx-auto text-blue-600 dark:text-blue-400 mb-3" />
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        {title || `${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)} Plan Required`}
      </h3>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
        {description || `This feature is available on our ${requiredTier} plan and above.`}
      </p>
      {onUpgrade && (
        <button
          onClick={onUpgrade}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 transition-colors font-medium"
        >
          Upgrade Now
        </button>
      )}
    </div>
  );
};

SubscriptionRequired.displayName = 'SubscriptionRequired';
