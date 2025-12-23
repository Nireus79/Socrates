/**
 * CommandPalette Component - Searchable command menu (Cmd+K)
 */

import React from 'react';
import { Command, Search, ChevronRight } from 'lucide-react';
import { Modal } from './dialog/Modal';

export interface Command {
  id: string;
  name: string;
  description?: string;
  icon?: React.ReactNode;
  category?: string;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  commands: Command[];
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  commands,
}) => {
  const [search, setSearch] = React.useState('');

  const filteredCommands = React.useMemo(() => {
    if (!search) return commands;

    const query = search.toLowerCase();
    return commands.filter(
      (cmd) =>
        cmd.name.toLowerCase().includes(query) ||
        cmd.description?.toLowerCase().includes(query) ||
        cmd.category?.toLowerCase().includes(query)
    );
  }, [search, commands]);

  const groupedCommands = React.useMemo(() => {
    const groups: Record<string, Command[]> = {};

    filteredCommands.forEach((cmd) => {
      const category = cmd.category || 'Other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(cmd);
    });

    return groups;
  }, [filteredCommands]);

  const handleCommand = (command: Command) => {
    command.action();
    setSearch('');
    onClose();
  };

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        // This would normally open the palette, but we'll let the parent handle it
      }
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md" className="top-1/4">
      <div className="space-y-0">
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <Search className="h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search commands..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
            className="flex-1 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-600 outline-none"
          />
          <kbd className="hidden sm:block px-2 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
            Esc
          </kbd>
        </div>

        {/* Commands List */}
        <div className="max-h-96 overflow-y-auto">
          {Object.keys(groupedCommands).length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-600 dark:text-gray-400">
                No commands found for "{search}"
              </p>
            </div>
          ) : (
            Object.entries(groupedCommands).map(([category, cmds]) => (
              <div key={category}>
                <div className="px-4 py-2 text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                  {category}
                </div>
                {cmds.map((cmd) => (
                  <button
                    key={cmd.id}
                    onClick={() => handleCommand(cmd)}
                    className="w-full px-4 py-2 flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
                  >
                    {cmd.icon && (
                      <div className="flex-shrink-0 text-gray-600 dark:text-gray-400">
                        {cmd.icon}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {cmd.name}
                      </p>
                      {cmd.description && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                          {cmd.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {cmd.shortcut && (
                        <kbd className="hidden sm:block px-2 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                          {cmd.shortcut}
                        </kbd>
                      )}
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    </div>
                  </button>
                ))}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
          {filteredCommands.length} command{filteredCommands.length !== 1 ? 's' : ''}
        </div>
      </div>
    </Modal>
  );
};

CommandPalette.displayName = 'CommandPalette';
