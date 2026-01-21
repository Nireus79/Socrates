/**
 * MainLayout Component - Main app layout with header and sidebar
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { NLUChatWidget } from '../nlu';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate();

  const handleNLUCommand = (command: string) => {
    const cmd = command.toLowerCase().trim();

    console.log('[MainLayout] Executing NLU command:', cmd);

    // Navigate to the requested page
    switch (cmd) {
      case '/dashboard':
        console.log('[MainLayout] Navigating to dashboard');
        navigate('/dashboard');
        break;
      case '/projects':
        console.log('[MainLayout] Navigating to projects');
        navigate('/projects');
        break;
      case '/chat':
        console.log('[MainLayout] Navigating to chat');
        navigate('/chat');
        break;
      case '/notes':
        console.log('[MainLayout] Navigating to notes');
        navigate('/notes');
        break;
      case '/knowledge':
        console.log('[MainLayout] Navigating to knowledge base');
        navigate('/knowledge');
        break;
      case '/analytics':
        console.log('[MainLayout] Navigating to analytics');
        navigate('/analytics');
        break;
      case '/search':
        console.log('[MainLayout] Navigating to search');
        navigate('/search');
        break;
      default:
        console.log('[MainLayout] Command handled in widget:', cmd);
    }
  };

  return (
    <div
      className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-950 relative"
    >
      {/* Semi-transparent overlay */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(circle at right bottom, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0) 70%)',
        }}
      />

      <Header />
      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar />
        <main className="flex-1 overflow-y-auto lg:ml-64">
          <div className="p-4 sm:p-5 md:p-6 lg:p-6 xl:p-8 w-full">
            {children}
          </div>
        </main>
      </div>
      <NLUChatWidget onCommandExecute={handleNLUCommand} />
    </div>
  );
};

MainLayout.displayName = 'MainLayout';
