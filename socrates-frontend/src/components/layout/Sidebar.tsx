/**
 * Sidebar Component - Left navigation menu
 */

import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  MessageSquare,
  Code2,
  BarChart3,
  Users,
  FileText,
  Settings,
  ChevronDown,
  Menu,
  X,
  BookOpen,
  Files,
  CheckSquare,
  Notebook,
  Search,
} from 'lucide-react';

interface NavItem {
  label: string;
  icon: React.ReactNode;
  path?: string;
  submenu?: NavItem[];
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    icon: <LayoutDashboard size={20} />,
    path: '/dashboard',
  },
  {
    label: 'Projects',
    icon: <FolderOpen size={20} />,
    path: '/projects',
  },
  {
    label: 'Dialogue',
    icon: <MessageSquare size={20} />,
    path: '/chat',
  },
  {
    label: 'Code Generation',
    icon: <Code2 size={20} />,
    path: '/code',
  },
  {
    label: 'Knowledge Base',
    icon: <BookOpen size={20} />,
    path: '/knowledge',
  },
  {
    label: 'Notes',
    icon: <Notebook size={20} />,
    path: '/notes',
  },
  {
    label: 'Search',
    icon: <Search size={20} />,
    path: '/search',
  },
  {
    label: 'Files',
    icon: <Files size={20} />,
    path: '/files',
  },
  {
    label: 'Analysis',
    icon: <CheckSquare size={20} />,
    path: '/analysis',
  },
  {
    label: 'Analytics',
    icon: <BarChart3 size={20} />,
    path: '/analytics',
  },
  {
    label: 'Collaboration',
    icon: <Users size={20} />,
    path: '/collaboration',
  },
  {
    label: 'Documentation',
    icon: <FileText size={20} />,
    path: '/docs',
  },
  {
    label: 'Settings',
    icon: <Settings size={20} />,
    path: '/settings',
  },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = React.useState(true);
  const [expandedItems, setExpandedItems] = React.useState<string[]>([]);

  const toggleExpand = (label: string) => {
    setExpandedItems((prev) =>
      prev.includes(label) ? prev.filter((item) => item !== label) : [...prev, label]
    );
  };

  const isActive = (path?: string) => {
    if (!path) return false;
    return location.pathname.startsWith(path);
  };

  return (
    <>
      {/* Toggle Button (Mobile) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-20 left-4 z-30 lg:hidden bg-white dark:bg-gray-900 p-2 rounded-lg border border-gray-200 dark:border-gray-800"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-16 bottom-0 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 overflow-y-auto transition-transform duration-300 z-20 lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`.trim()}
      >
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <div key={item.label}>
              <button
                onClick={() => {
                  if (item.path) {
                    navigate(item.path);
                    setIsOpen(false);
                  } else if (item.submenu) {
                    toggleExpand(item.label);
                  }
                }}
                className={`w-full flex items-center justify-between px-4 py-2.5 rounded-lg transition-colors ${
                  isActive(item.path)
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`.trim()}
              >
                <div className="flex items-center gap-3">
                  {item.icon}
                  <span>{item.label}</span>
                </div>
                {item.submenu && (
                  <ChevronDown
                    size={16}
                    className={`transition-transform ${
                      expandedItems.includes(item.label) ? 'rotate-180' : ''
                    }`.trim()}
                  />
                )}
              </button>

              {/* Submenu */}
              {item.submenu && expandedItems.includes(item.label) && (
                <div className="ml-4 mt-1 space-y-1">
                  {item.submenu.map((subitem) => (
                    <button
                      key={subitem.label}
                      onClick={() => {
                        if (subitem.path) {
                          navigate(subitem.path);
                          setIsOpen(false);
                        }
                      }}
                      className={`w-full flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
                        isActive(subitem.path)
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`.trim()}
                    >
                      {subitem.icon}
                      {subitem.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
};

Sidebar.displayName = 'Sidebar';
