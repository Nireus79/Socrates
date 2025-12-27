/**
 * NotesPage - Project notes management
 */

import React from 'react';
import { Search, AlertCircle } from 'lucide-react';
import { useProjectStore } from '../../stores';
import { useNotesStore } from '../../stores/notesStore';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card, Alert, Input, Button, Tab } from '../../components/common';
import { NoteForm, NotesGrid } from '../../components/notes';

type TabType = 'all' | 'search';

export const NotesPage: React.FC = () => {
  const { projects, listProjects } = useProjectStore();
  const {
    notes,
    selectedProjectId,
    isLoading,
    error,
    searchQuery,
    searchResults,
    setSelectedProject,
    fetchNotes,
    createNote,
    deleteNote,
    searchNotes,
    clearError,
    clearSearch,
  } = useNotesStore();

  const [activeTab, setActiveTab] = React.useState<TabType>('all');
  const [localSearchQuery, setLocalSearchQuery] = React.useState('');
  const [isSearching, setIsSearching] = React.useState(false);

  // Load projects on mount
  React.useEffect(() => {
    listProjects();
  }, [listProjects]);

  // Handle search
  const handleSearch = React.useCallback(async () => {
    if (!selectedProjectId || !localSearchQuery.trim()) {
      clearSearch();
      return;
    }

    setIsSearching(true);
    try {
      await searchNotes(selectedProjectId, localSearchQuery);
      setActiveTab('search');
    } finally {
      setIsSearching(false);
    }
  }, [selectedProjectId, localSearchQuery, searchNotes, clearSearch]);

  // Handle Enter key in search
  const handleSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  // Handle clear search
  const handleClearSearch = () => {
    setLocalSearchQuery('');
    clearSearch();
    setActiveTab('all');
  };

  // Handle project change
  const handleProjectChange = (projectId: string) => {
    setSelectedProject(projectId);
    clearSearch();
    setLocalSearchQuery('');
    setActiveTab('all');
  };

  // Handle create note
  const handleCreateNote = async (title: string, content: string, tags: string[]) => {
    if (!selectedProjectId) {
      alert('Please select a project first');
      return;
    }

    await createNote(selectedProjectId, title, content, tags);
  };

  // Handle delete note
  const handleDeleteNote = async (noteId: string) => {
    if (!selectedProjectId) return;

    if (window.confirm('Are you sure you want to delete this note?')) {
      await deleteNote(selectedProjectId, noteId);
    }
  };

  // Clear errors on unmount
  React.useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  const displayNotes = activeTab === 'search' ? searchResults : notes;

  return (
    <MainLayout>
      <PageHeader
        title="Notes"
        description="Manage and organize your project notes"
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - Project Selection */}
        <div className="lg:col-span-1">
          <Card>
            <div className="p-4">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
                Projects
              </h3>

              {projects.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No projects available
                </p>
              ) : (
                <div className="space-y-2">
                  {projects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() => handleProjectChange(project.id)}
                      className={`w-full text-left px-3 py-2 rounded text-sm font-medium transition-colors ${
                        selectedProjectId === project.id
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      {project.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {!selectedProjectId ? (
            <Alert type="info" title="Select a Project">
              Please select a project from the sidebar to start managing notes
            </Alert>
          ) : (
            <>
              {/* Error Message */}
              {error && (
                <Alert type="error" title="Error" onClose={clearError} className="mb-6">
                  {error}
                </Alert>
              )}

              {/* Note Form */}
              <NoteForm
                onSubmit={handleCreateNote}
                isSubmitting={isLoading}
                error={error}
              />

              {/* Search Bar */}
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
                <div className="flex gap-2">
                  <Input
                    value={localSearchQuery}
                    onChange={(e) => setLocalSearchQuery(e.target.value)}
                    onKeyPress={handleSearchKeyPress}
                    placeholder="Search notes..."
                    disabled={isSearching}
                    icon={<Search className="h-4 w-4" />}
                  />
                  <Button
                    variant="secondary"
                    onClick={handleSearch}
                    disabled={isSearching || !localSearchQuery.trim()}
                  >
                    Search
                  </Button>
                  {searchQuery && (
                    <Button
                      variant="outline"
                      onClick={handleClearSearch}
                      disabled={isSearching}
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </div>

              {/* Tabs */}
              {searchQuery && (
                <div className="flex gap-2 mb-4 border-b border-gray-200 dark:border-gray-700">
                  <button
                    onClick={() => setActiveTab('all')}
                    className={`px-4 py-2 font-medium transition-colors ${
                      activeTab === 'all'
                        ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
                    }`}
                  >
                    All Notes ({notes.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('search')}
                    className={`px-4 py-2 font-medium transition-colors ${
                      activeTab === 'search'
                        ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
                    }`}
                  >
                    Search Results ({searchResults.length})
                  </button>
                </div>
              )}

              {/* Notes Grid */}
              <NotesGrid
                notes={displayNotes}
                isLoading={isLoading}
                onDelete={handleDeleteNote}
              />
            </>
          )}
        </div>
      </div>
    </MainLayout>
  );
};
