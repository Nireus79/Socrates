/**
 * Tooltip Component - Hover tooltip
 */

import React from 'react';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 200,
}) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const [isDelayed, setIsDelayed] = React.useState(false);
  const timeoutRef = React.useRef<any>(null);

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsDelayed(true);
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsVisible(false);
    setIsDelayed(false);
  };

  const positionClasses = {
    top: 'bottom-full mb-2 left-1/2 -translate-x-1/2',
    bottom: 'top-full mt-2 left-1/2 -translate-x-1/2',
    left: 'right-full mr-2 top-1/2 -translate-y-1/2',
    right: 'left-full ml-2 top-1/2 -translate-y-1/2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-gray-900 dark:border-t-gray-700 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent',
    bottom:
      'bottom-full left-1/2 -translate-x-1/2 border-b-gray-900 dark:border-b-gray-700 border-l-4 border-r-4 border-b-8 border-l-transparent border-r-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-gray-900 dark:border-l-gray-700 border-t-4 border-b-4 border-l-8 border-t-transparent border-b-transparent',
    right:
      'right-full top-1/2 -translate-y-1/2 border-r-gray-900 dark:border-r-gray-700 border-t-4 border-b-4 border-r-8 border-t-transparent border-b-transparent',
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}

      {isVisible && isDelayed && (
        <div className={`absolute z-50 ${positionClasses[position]} pointer-events-none`.trim()}>
          <div className="bg-gray-900 dark:bg-gray-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
            {content}
          </div>
          <div className={`absolute ${arrowClasses[position]}`.trim()} />
        </div>
      )}
    </div>
  );
};

Tooltip.displayName = 'Tooltip';
