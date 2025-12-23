/**
 * Dropdown Component - Dropdown menu
 */

import React from 'react';
import { ChevronDown } from 'lucide-react';

interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  variant?: 'default' | 'danger';
  divider?: boolean;
}

interface DropdownProps {
  items?: DropdownItem[];
  trigger: React.ReactNode;
  align?: 'left' | 'right';
  children?: React.ReactNode;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Dropdown: React.FC<DropdownProps> = ({
  items = [],
  trigger,
  align = 'left',
  children,
  isOpen: controlledIsOpen,
  onClose,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        const newIsOpen = false;
        setIsOpen(newIsOpen);
        if (!controlledIsOpen) {
          onClose?.();
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [controlledIsOpen, onClose]);

  const handleItemClick = (onClick?: () => void) => {
    onClick?.();
    if (controlledIsOpen === undefined) {
      setIsOpen(false);
    }
    onClose?.();
  };

  const isOpenState = controlledIsOpen !== undefined ? controlledIsOpen : isOpen;
  const alignmentClass = align === 'right' ? 'right-0' : 'left-0';

  return (
    <div ref={dropdownRef} className="relative inline-block">
      <div
        onClick={() => {
          if (controlledIsOpen === undefined) {
            setIsOpen(!isOpen);
          }
        }}
        className="inline-block"
      >
        {trigger}
      </div>

      {isOpenState && (
        <div
          className={`absolute top-full ${alignmentClass} mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50`.trim()}
        >
          <div className="py-1">
            {children ? (
              children
            ) : (
              items.map((item) => (
                <React.Fragment key={item.id}>
                  {item.divider && (
                    <div className="my-1 border-t border-gray-200 dark:border-gray-700" />
                  )}
                  <button
                    onClick={() => handleItemClick(item.onClick)}
                    className={`w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors ${
                      item.variant === 'danger'
                        ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`.trim()}
                  >
                    {item.icon && <span>{item.icon}</span>}
                    <span>{item.label}</span>
                  </button>
                </React.Fragment>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

Dropdown.displayName = 'Dropdown';
