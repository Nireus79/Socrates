/**
 * Popover Component - Floating popover
 */

import React from 'react';

type PopoverPosition = 'top' | 'bottom' | 'left' | 'right';

interface PopoverProps {
  isOpen: boolean;
  onClose: () => void;
  trigger: React.ReactNode;
  children: React.ReactNode;
  position?: PopoverPosition;
}

const positionClasses: Record<PopoverPosition, string> = {
  top: 'bottom-full mb-2',
  bottom: 'top-full mt-2',
  left: 'right-full mr-2',
  right: 'left-full ml-2',
};

export const Popover: React.FC<PopoverProps> = ({
  isOpen,
  onClose,
  trigger,
  children,
  position = 'bottom',
}) => {
  const popoverRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  return (
    <div ref={popoverRef} className="relative inline-block">
      <div onClick={(e) => e.stopPropagation()}>{trigger}</div>

      {isOpen && (
        <div
          className={`absolute z-50 ${positionClasses[position]} bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 min-w-max`.trim()}
        >
          {children}
        </div>
      )}
    </div>
  );
};

Popover.displayName = 'Popover';
