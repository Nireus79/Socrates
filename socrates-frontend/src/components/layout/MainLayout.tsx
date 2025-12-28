/**
 * MainLayout Component - Main app layout with header and sidebar
 */

import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
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
          <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

MainLayout.displayName = 'MainLayout';
