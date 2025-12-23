/**
 * Sheet Component - Side panel
 */

import React from 'react';
import { X } from 'lucide-react';

interface SheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  side?: 'left' | 'right';
  width?: 'sm' | 'md' | 'lg';
}

const widths = {
  sm: 'w-64',
  md: 'w-96',
  lg: 'w-[500px]',
};

export const Sheet: React.FC<SheetProps> = ({
  isOpen,
  onClose,
  title,
  children,
  side = 'right',
  width = 'md',
}) => {
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sideClass = side === 'left' ? 'left-0' : 'right-0';
  const slideClass =
    side === 'left'
      ? 'translate-x-0 group-data-[side=left]:-translate-x-full'
      : 'translate-x-0 group-data-[side=right]:translate-x-full';

  return (
    <div className="fixed inset-0 z-50 flex" data-side={side}>
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sheet */}
      <div
        className={`relative ml-auto ${sideClass} bg-white dark:bg-gray-900 shadow-xl h-full overflow-y-auto transition-transform duration-300 ${widths[width]} ${slideClass}`.trim()}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800 sticky top-0 bg-white dark:bg-gray-900">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {title}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
            >
              <X size={24} />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

Sheet.displayName = 'Sheet';
