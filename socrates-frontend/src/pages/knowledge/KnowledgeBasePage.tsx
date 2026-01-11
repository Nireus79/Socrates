/**
 * KnowledgeBasePage - Knowledge base management and import
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Upload, Trash2, Search, Plus } from 'lucide-react';
import { useProjectStore } from '../../stores';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { showSuccess, showError, showInfo } from '../../stores/notificationStore';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card, Tab, Alert, LoadingSpinner, Button, Input, SkeletonList, ErrorBoundary } from '../../components/common';
import { NLUChatWidget } from '../../components/nlu';
import DocumentFilters from '../../components/knowledge/DocumentFilters';
import DocumentBulkActions from '../../components/knowledge/DocumentBulkActions';
import BulkImportModal from '../../components/knowledge/BulkImportModal';
import { DocumentCard } from '../../components/knowledge/DocumentCard';
import { NoteCard } from '../../components/knowledge/NoteCard';
import { GitHubRepositoryCard } from '../../components/knowledge/GitHubRepositoryCard';
import DocumentDetailsModal from '../../components/knowledge/DocumentDetailsModal';
import { knowledgeAPI } from '../../api/knowledge';

export const KnowledgeBasePage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const {
    projects,
    currentProject,
    isLoading: projectLoading,
    getProject,
    listProjects,
  } = useProjectStore();

  const {
    documents,
    searchResults,
    currentQuery,
    isLoading,
    isImporting,
    isSearching,
    error,
    listDocuments,
    loadDocuments,
    importFile,
    importURL,
    importText,
    searchKnowledge,
    deleteDocument,
    addKnowledgeEntry,
    clearError,
    clearSearch,
    selectedDocuments,
    toggleDocumentSelection,
    clearSelection,
  } = useKnowledgeStore();

  const [selectedProjectId, setSelectedProjectId] = React.useState(projectId || '');
  const [activeTab, setActiveTab] = React.useState('documents');
  const [fileInput, setFileInput] = React.useState<HTMLInputElement | null>(null);
  const [importUrl, setImportUrl] = React.useState('');
  const [importTitle, setImportTitle] = React.useState('');
  const [importContent, setImportContent] = React.useState('');
  const [searchQuery, setSearchQuery] = React.useState('');
  const [entryContent, setEntryContent] = React.useState('');
  const [entryCategory, setEntryCategory] = React.useState('general');
  const [showBulkImportModal, setShowBulkImportModal] = React.useState(false);
  const [allSources, setAllSources] = React.useState<any>(null);
  const [loadingAllSources, setLoadingAllSources] = React.useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = React.useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = React.useState(false);

  // Load projects on mount
  React.useEffect(() => {
    listProjects();
  }, [listProjects]);

  // Update selectedProjectId when URL projectId changes
  React.useEffect(() => {
    if (projectId) {
      setSelectedProjectId(projectId);
    }
  }, [projectId]);

  // Load project and documents when selectedProjectId changes
  React.useEffect(() => {
    if (selectedProjectId) {
      getProject(selectedProjectId);
      listDocuments(selectedProjectId);
      // Load all knowledge sources (documents, notes, repos)
      loadAllKnowledgeSources();
    }
  }, [selectedProjectId, getProject, listDocuments]);

  // Clear errors on unmount
  React.useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  // Handle file import
  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && selectedProjectId) {
      try {
        await importFile(file, selectedProjectId);
        // Reset input
        if (fileInput) fileInput.value = '';
      } catch (err) {
        console.error('File import failed:', err);
      }
    }
  };

  // Handle URL import
  const handleImportURL = async () => {
    if (!importUrl || !selectedProjectId) return;
    try {
      await importURL(importUrl, selectedProjectId);
      setImportUrl('');
    } catch (err) {
      console.error('URL import failed:', err);
    }
  };

  // Handle text import
  const handleImportText = async () => {
    if (!importTitle || !importContent || !selectedProjectId) return;
    try {
      await importText(importTitle, importContent, selectedProjectId);
      setImportTitle('');
      setImportContent('');
    } catch (err) {
      console.error('Text import failed:', err);
    }
  };

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery || !selectedProjectId) return;
    try {
      await searchKnowledge(searchQuery, selectedProjectId);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  // Load all knowledge sources (documents, notes, repos)
  const loadAllKnowledgeSources = async () => {
    if (!selectedProjectId) return;
    try {
      setLoadingAllSources(true);
      const response = await knowledgeAPI.getAllKnowledgeSources(selectedProjectId);
      setAllSources(response.data?.sources);
    } catch (err) {
      console.error('Failed to load knowledge sources:', err);
    } finally {
      setLoadingAllSources(false);
    }
  };

  // Handle document delete
  const handleDeleteDocument = async (documentId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await deleteDocument(documentId);
      // Refresh documents after deletion
      await listDocuments(selectedProjectId);
      loadAllKnowledgeSources();
      showSuccess('Document Deleted', 'The document has been successfully removed from your knowledge base');
    } catch (err) {
      console.error('Delete failed:', err);
      showError('Delete Failed', 'There was an error deleting the document. Please try again.');
    }
  };

  // Handle add knowledge entry
  const handleAddEntry = async () => {
    if (!entryContent || !selectedProjectId) return;
    try {
      await addKnowledgeEntry(entryContent, entryCategory, selectedProjectId);
      setEntryContent('');
      setEntryCategory('general');
      showSuccess('Entry Added', 'Your knowledge entry has been added successfully');
    } catch (err) {
      console.error('Add entry failed:', err);
      showError('Failed to Add Entry', 'There was an error adding the knowledge entry. Please try again.');
    }
  };

  const tabs = [
    { label: 'Documents', value: 'documents' },
    { label: 'Notes', value: 'notes' },
    { label: 'GitHub', value: 'github' },
    { label: 'Import', value: 'import' },
    { label: 'Search', value: 'search' },
    { label: 'Entries', value: 'entries' },
  ];

  return (
    <ErrorBoundary>
      <MainLayout>
        <div className="space-y-8">
        {/* Error Alert */}
        {error && (
          <Alert type="error" title="Error">
            {error}
          </Alert>
        )}

        {/* Project Selector */}
        {!selectedProjectId && projects.length === 0 ? (
          <Alert type="info" title="No Projects">
            You don't have any projects yet. Create a project first to manage its knowledge base.
          </Alert>
        ) : (
          <>
            <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 dark:from-blue-900 dark:to-indigo-900 dark:border-blue-800">
              <div className="flex items-center gap-3">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">
                  Project:
                </label>
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="">-- Choose a Project --</option>
                  {projects.length > 0 ? (
                    projects.map((project) => (
                      <option key={project.project_id} value={project.project_id}>
                        {project.name} {selectedProjectId === project.project_id ? '(Current)' : ''}
                      </option>
                    ))
                  ) : (
                    <option disabled>No projects available</option>
                  )}
                </select>
                {currentProject && (
                  <div className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                    Phase: <span className="font-semibold capitalize">{currentProject.phase || 'N/A'}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* Header */}
            <PageHeader
              title="Knowledge Base"
              description="Manage your project's knowledge base documents and entries"
              breadcrumbs={[
                { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
                { label: 'Knowledge Base' },
              ]}
            />

            {/* Show tabs only if project is selected */}
            {!selectedProjectId ? (
              <Alert type="info" title="Select a Project">
                Choose a project from the dropdown above to manage its knowledge base.
              </Alert>
            ) : (
              <>
                {/* Tabs */}
                <Card>
                  <Tab
                    tabs={tabs}
                    activeTab={activeTab}
                    onChange={setActiveTab}
                    variant="default"
                  />
                </Card>

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            {/* Filters */}
            <DocumentFilters />

            {/* Bulk Actions */}
            {documents.size > 0 && (
              <DocumentBulkActions
                selectedCount={selectedDocuments.size}
                totalCount={documents.size}
                onBulkImportClick={() => setShowBulkImportModal(true)}
                projectId={selectedProjectId}
              />
            )}

            {/* Documents Grid */}
            {isLoading && documents.size === 0 ? (
              <SkeletonList count={4} height="100px" />
            ) : documents.size > 0 ? (
              <div className="grid gap-4">
                {Array.from(documents.values()).map((doc) => (
                  <DocumentCard
                    key={doc.id}
                    document={doc}
                    isSelected={selectedDocuments.has(doc.id)}
                    onSelect={(selected) => toggleDocumentSelection(doc.id)}
                    onDelete={() => handleDeleteDocument(doc.id)}
                    onView={() => {
                      setSelectedDocumentId(doc.id);
                      setIsModalOpen(true);
                    }}
                  />
                ))}
              </div>
            ) : (
              <Alert type="info" title="No Documents">
                No documents in your knowledge base yet. Use the Import tab to add content.
              </Alert>
            )}

            {/* Bulk Import Modal */}
            <BulkImportModal
              isOpen={showBulkImportModal}
              onClose={() => setShowBulkImportModal(false)}
              projectId={selectedProjectId}
            />
          </div>
        )}

        {/* Notes Tab */}
        {activeTab === 'notes' && (
          <div className="space-y-6">
            {loadingAllSources ? (
              <SkeletonList count={3} height="150px" />
            ) : allSources?.notes && allSources.notes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {allSources.notes.map((note: any) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    onDelete={() => {
                      if (window.confirm('Delete this note?')) {
                        // Note deletion would be implemented via API
                        showInfo('Note', 'Note deletion will be available soon');
                      }
                    }}
                    onEdit={() => {
                      showInfo('Note', 'Note editing will be available soon');
                    }}
                  />
                ))}
              </div>
            ) : (
              <Alert type="info" title="No Notes">
                You haven't created any notes yet. Add notes from your project settings.
              </Alert>
            )}
          </div>
        )}

        {/* GitHub Repositories Tab */}
        {activeTab === 'github' && (
          <div className="space-y-6">
            {loadingAllSources ? (
              <SkeletonList count={2} height="200px" />
            ) : allSources?.repositories && allSources.repositories.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {allSources.repositories.map((repo: any) => (
                  <GitHubRepositoryCard
                    key={repo.id}
                    repo={repo}
                    onSync={() => {
                      showInfo('GitHub', 'Repository sync will be available soon');
                    }}
                    onDelete={() => {
                      if (window.confirm('Remove this repository from your project?')) {
                        showInfo('GitHub', 'Repository removal will be available soon');
                      }
                    }}
                  />
                ))}
              </div>
            ) : (
              <Alert type="info" title="No GitHub Repositories">
                You haven't imported any GitHub repositories yet. Use the Projects page to import a repository.
              </Alert>
            )}
          </div>
        )}

        {/* Import Tab */}
        {activeTab === 'import' && (
          <div className="space-y-6">
            {/* File Import */}
            <Card>
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Import File
                </h3>
                <div className="flex gap-2">
                  <input
                    ref={setFileInput}
                    type="file"
                    onChange={handleImportFile}
                    disabled={isImporting}
                    className="hidden"
                    accept=".pdf,.txt,.doc,.docx"
                    id="file-input"
                  />
                  <label className="flex-1" htmlFor="file-input">
                    <span className="block w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900 truncate">
                      {fileInput?.files?.[0]?.name || 'Choose file...'}
                    </span>
                  </label>
                  <Button
                    onClick={() => fileInput?.click()}
                    disabled={isImporting}
                    variant="primary"
                    className="flex items-center gap-2 whitespace-nowrap"
                  >
                    <Upload size={18} />
                    {isImporting ? 'Uploading...' : 'Upload'}
                  </Button>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Supported formats: PDF, TXT, DOC, DOCX
                </p>
              </div>
            </Card>

            {/* URL Import */}
            <Card>
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Import from URL
                </h3>
                <div className="flex gap-2">
                  <Input
                    type="url"
                    placeholder="https://example.com/article"
                    value={importUrl}
                    onChange={(e) => setImportUrl(e.target.value)}
                    disabled={isImporting}
                  />
                  <Button
                    onClick={handleImportURL}
                    disabled={isImporting || !importUrl}
                    variant="primary"
                    className="flex items-center gap-2"
                  >
                    <Upload size={18} />
                    {isImporting ? 'Importing...' : 'Import'}
                  </Button>
                </div>
              </div>
            </Card>

            {/* Text Import */}
            <Card>
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Import Text
                </h3>
                <Input
                  placeholder="Title"
                  value={importTitle}
                  onChange={(e) => setImportTitle(e.target.value)}
                  disabled={isImporting}
                />
                <textarea
                  placeholder="Paste your content here..."
                  value={importContent}
                  onChange={(e) => setImportContent(e.target.value)}
                  disabled={isImporting}
                  className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                  rows={6}
                />
                <Button
                  onClick={handleImportText}
                  disabled={isImporting || !importTitle || !importContent}
                  variant="primary"
                  className="flex items-center gap-2"
                >
                  <Plus size={18} />
                  {isImporting ? 'Adding...' : 'Add Text'}
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <Card>
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Search Knowledge Base
                </h3>
                <div className="flex gap-2">
                  <Input
                    placeholder="Search your knowledge base..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') handleSearch();
                    }}
                    disabled={isSearching}
                  />
                  <Button
                    onClick={handleSearch}
                    disabled={isSearching || !searchQuery}
                    variant="primary"
                    className="flex items-center gap-2"
                  >
                    <Search size={18} />
                    {isSearching ? 'Searching...' : 'Search'}
                  </Button>
                </div>
              </div>
            </Card>

            {/* Search Results */}
            {isSearching ? (
              <div className="flex justify-center py-12">
                <LoadingSpinner size="lg" />
              </div>
            ) : searchResults.length > 0 ? (
              <div className="grid gap-4">
                {searchResults.map((result, index) => (
                  <Card key={`search-${index}-${result.title}`}>
                    <div className="space-y-2">
                      <h4 className="font-semibold text-gray-900 dark:text-white">
                        {result.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {result.excerpt}
                      </p>
                      <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-500">
                        <span>
                          Relevance: {(result.relevance_score * 100).toFixed(1)}%
                        </span>
                        <span>Source: {result.source}</span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : currentQuery ? (
              <Alert type="info" title="No Results">
                No documents found matching "{currentQuery}". Try different keywords.
              </Alert>
            ) : null}
          </div>
        )}

        {/* Entries Tab */}
        {activeTab === 'entries' && (
          <div className="space-y-6">
            <Card>
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Add Knowledge Entry
                </h3>
                <select
                  value={entryCategory}
                  onChange={(e) => setEntryCategory(e.target.value)}
                  disabled={isLoading}
                  className="w-full p-2 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white bg-white dark:bg-gray-900"
                >
                  <option value="general">General</option>
                  <option value="best-practices">Best Practices</option>
                  <option value="technical">Technical</option>
                  <option value="documentation">Documentation</option>
                  <option value="design-patterns">Design Patterns</option>
                  <option value="architecture">Architecture</option>
                </select>
                <textarea
                  placeholder="Enter your knowledge entry..."
                  value={entryContent}
                  onChange={(e) => setEntryContent(e.target.value)}
                  disabled={isLoading}
                  className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white bg-white dark:bg-gray-900 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                  rows={8}
                />
                <Button
                  onClick={handleAddEntry}
                  disabled={isLoading || !entryContent}
                  variant="primary"
                  className="flex items-center gap-2"
                >
                  <Plus size={18} />
                  {isLoading ? 'Adding...' : 'Add Entry'}
                </Button>
              </div>
            </Card>

            <Alert type="info" title="Knowledge Entries">
              Knowledge entries are manually created snippets of information. They are categorized
              and searchable alongside your imported documents.
            </Alert>
          </div>
        )}
              </>
            )}
          </>
        )}
      </div>

      {/* Document Details Modal */}
      <DocumentDetailsModal
        documentId={selectedDocumentId || ''}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedDocumentId(null);
        }}
        onDelete={() => {
          if (selectedDocumentId) {
            handleDeleteDocument(selectedDocumentId);
            setIsModalOpen(false);
            setSelectedDocumentId(null);
          }
        }}
      />

      {/* NLU Chat Widget */}
      <NLUChatWidget
        initiallyOpen={false}
        context={{ project_id: selectedProjectId }}
        onCommandExecute={(command) => {
          // Command execution handled by slash commands
          console.log('Command executed:', command);
        }}
      />
      </MainLayout>
    </ErrorBoundary>
  );
};
