/**
 * KnowledgeBasePage - Knowledge base management and import
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Upload, Trash2, Search, Plus } from 'lucide-react';
import { useProjectStore } from '../../stores';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card, Tab, Alert, LoadingSpinner, Button, Input } from '../../components/common';

export const KnowledgeBasePage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const { currentProject } = useProjectStore();

  const {
    documents,
    searchResults,
    currentQuery,
    isLoading,
    isImporting,
    isSearching,
    error,
    listDocuments,
    importFile,
    importURL,
    importText,
    searchKnowledge,
    deleteDocument,
    addKnowledgeEntry,
    clearError,
    clearSearch,
  } = useKnowledgeStore();

  const [activeTab, setActiveTab] = React.useState('documents');
  const [fileInput, setFileInput] = React.useState<HTMLInputElement | null>(null);
  const [importUrl, setImportUrl] = React.useState('');
  const [importTitle, setImportTitle] = React.useState('');
  const [importContent, setImportContent] = React.useState('');
  const [searchQuery, setSearchQuery] = React.useState('');
  const [entryContent, setEntryContent] = React.useState('');
  const [entryCategory, setEntryCategory] = React.useState('general');

  // Load documents on mount
  React.useEffect(() => {
    if (projectId) {
      listDocuments(projectId);
    }
  }, [projectId, listDocuments]);

  // Clear errors on unmount
  React.useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  // Handle file import
  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && projectId) {
      try {
        await importFile(file, projectId);
        // Reset input
        if (fileInput) fileInput.value = '';
      } catch (err) {
        console.error('File import failed:', err);
      }
    }
  };

  // Handle URL import
  const handleImportURL = async () => {
    if (!importUrl || !projectId) return;
    try {
      await importURL(importUrl, projectId);
      setImportUrl('');
    } catch (err) {
      console.error('URL import failed:', err);
    }
  };

  // Handle text import
  const handleImportText = async () => {
    if (!importTitle || !importContent || !projectId) return;
    try {
      await importText(importTitle, importContent, projectId);
      setImportTitle('');
      setImportContent('');
    } catch (err) {
      console.error('Text import failed:', err);
    }
  };

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery || !projectId) return;
    try {
      await searchKnowledge(searchQuery, projectId);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  // Handle document delete
  const handleDeleteDocument = async (documentId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await deleteDocument(documentId);
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  // Handle add knowledge entry
  const handleAddEntry = async () => {
    if (!entryContent || !projectId) return;
    try {
      await addKnowledgeEntry(entryContent, entryCategory, projectId);
      setEntryContent('');
      setEntryCategory('general');
    } catch (err) {
      console.error('Add entry failed:', err);
    }
  };

  const tabs = [
    { label: 'Documents', value: 'documents' },
    { label: 'Import', value: 'import' },
    { label: 'Search', value: 'search' },
    { label: 'Entries', value: 'entries' },
  ];

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Error Alert */}
        {error && (
          <Alert type="error" title="Error">
            {error}
          </Alert>
        )}

        {/* Header */}
        <PageHeader
          title="Knowledge Base"
          description="Manage your project's knowledge base documents and entries"
          breadcrumbs={[
            { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
            { label: 'Knowledge Base' },
          ]}
        />

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
            {isLoading ? (
              <div className="flex justify-center py-12">
                <LoadingSpinner size="lg" />
              </div>
            ) : documents.size > 0 ? (
              <div className="grid gap-4">
                {Array.from(documents.values()).map((doc) => (
                  <Card key={doc.id} className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {doc.title}
                      </h3>
                      <div className="mt-2 flex gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <span>Type: {doc.source_type}</span>
                        <span>Chunks: {doc.chunk_count}</span>
                        {doc.size && <span>Size: {(doc.size / 1024).toFixed(2)} KB</span>}
                        <span>
                          Added: {new Date(doc.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Button
                      onClick={() => handleDeleteDocument(doc.id)}
                      variant="danger"
                      size="sm"
                      className="flex items-center gap-2"
                    >
                      <Trash2 size={16} />
                      Delete
                    </Button>
                  </Card>
                ))}
              </div>
            ) : (
              <Alert type="info" title="No Documents">
                No documents in your knowledge base yet. Use the Import tab to add content.
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
                    className="flex-1"
                    accept=".pdf,.txt,.doc,.docx"
                  />
                  <Button
                    disabled={isImporting}
                    variant="primary"
                    className="flex items-center gap-2"
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
      </div>
    </MainLayout>
  );
};
