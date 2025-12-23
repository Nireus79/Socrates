/**
 * Accordion Component - Expandable sections
 */

import React from 'react';
import { ChevronDown } from 'lucide-react';

interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
  icon?: React.ReactNode;
}

interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
  onChange?: (expandedIds: string[]) => void;
}

export const Accordion: React.FC<AccordionProps> = ({
  items,
  allowMultiple = false,
  onChange,
}) => {
  const [expandedIds, setExpandedIds] = React.useState<string[]>([]);

  const toggleItem = (id: string) => {
    let newExpandedIds: string[];

    if (allowMultiple) {
      newExpandedIds = expandedIds.includes(id)
        ? expandedIds.filter((expandedId) => expandedId !== id)
        : [...expandedIds, id];
    } else {
      newExpandedIds = expandedIds.includes(id) ? [] : [id];
    }

    setExpandedIds(newExpandedIds);
    onChange?.(newExpandedIds);
  };

  return (
    <div className="space-y-2 border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden">
      {items.map((item, index) => (
        <div
          key={item.id}
          className={index > 0 ? 'border-t border-gray-200 dark:border-gray-800' : ''}
        >
          <button
            onClick={() => toggleItem(item.id)}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              {item.icon && <span>{item.icon}</span>}
              <span className="font-medium text-gray-900 dark:text-white">
                {item.title}
              </span>
            </div>
            <ChevronDown
              size={20}
              className={`text-gray-500 transition-transform ${
                expandedIds.includes(item.id) ? 'rotate-180' : ''
              }`.trim()}
            />
          </button>

          {expandedIds.includes(item.id) && (
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 text-gray-700 dark:text-gray-300">
              {item.content}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

Accordion.displayName = 'Accordion';
