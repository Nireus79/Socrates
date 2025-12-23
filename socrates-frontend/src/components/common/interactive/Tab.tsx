/**
 * Tab Component - Tabbed content interface
 */

import React from 'react';

interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

interface TabProps {
  items?: TabItem[];
  tabs?: Array<{ label: string; value: string }>;
  defaultTab?: string;
  activeTab?: string;
  onChange?: (tabId: string) => void;
  variant?: 'default' | 'pills';
}

export const Tab: React.FC<TabProps> = ({
  items,
  tabs,
  defaultTab,
  activeTab: controlledActiveTab,
  onChange,
  variant = 'default',
}) => {
  const [internalActiveTab, setInternalActiveTab] = React.useState(
    defaultTab || items?.[0]?.id || tabs?.[0]?.value || ''
  );

  const isControlled = controlledActiveTab !== undefined;
  const activeTab = isControlled ? controlledActiveTab : internalActiveTab;
  const tabItems = items || tabs?.map(t => ({ id: t.value, label: t.label })) || [];

  const handleTabChange = (tabId: string) => {
    if (!isControlled) {
      setInternalActiveTab(tabId);
    }
    onChange?.(tabId);
  };

  const baseTabStyles = 'flex items-center gap-2 px-4 py-2 font-medium transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed';

  const tabStyles = {
    default: {
      container: 'border-b border-gray-200 dark:border-gray-800',
      button: (isActive: boolean) =>
        isActive
          ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300',
    },
    pills: {
      container: 'gap-2',
      button: (isActive: boolean) =>
        isActive
          ? 'bg-blue-600 dark:bg-blue-500 text-white rounded-full'
          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full',
    },
  };

  const style = tabStyles[variant];

  return (
    <div className="w-full">
      {/* Tab List */}
      <div className={`flex overflow-x-auto ${style.container}`.trim()}>
        {tabItems.map((item) => (
          <button
            key={item.id}
            onClick={() => handleTabChange(item.id)}
            disabled={'disabled' in item ? (item as TabItem).disabled : false}
            className={`${baseTabStyles} ${style.button(activeTab === item.id)}`.trim()}
          >
            {'icon' in item && (item as TabItem).icon && <span>{(item as TabItem).icon}</span>}
            <span>{item.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {items && items.find((item) => item.id === activeTab)?.content}
      </div>
    </div>
  );
};

Tab.displayName = 'Tab';
