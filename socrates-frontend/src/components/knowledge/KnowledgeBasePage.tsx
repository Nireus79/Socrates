/**
 * Knowledge Base Page - Main knowledge management interface
 *
 * Features:
 * - Document list with metadata
 * - Document import (file, URL, text)
 * - Full-text search
 * - Document deletion
 */

import React from 'react';
import {
  Plus,
  Search,
  Upload,
  Link,
  FileText,
  Trash2,
  Loader,
} from 'lucide-react';
import { useKnowledgeStore } from '../../stores';
import { Button } from '../common';
import { Input } from '../common';
import { Alert } from '../common';
import { Card } from '../common';
import { DocumentCard } from './DocumentCard';
import { ImportModal } from './ImportModal';
import { SearchPanel } from './SearchPanel';

interface KnowledgeBasePageProps {
  projectId?: string;
}

export const KnowledgeBasePage: React.FC<KnowledgeBasePageProps> = ({
  projectId,
}) => {
  const {
    documents,
    searchResults,
    currentQuery,
    isLoading,
    isSearching,
    error,
    listDocuments,
    deleteDocument,
    clearError,
  } = useKnowledgeStore();

  const [isImportModalOpen, setIsImportModalOpen] = React.useState(false);
  const [showSearchResults, setShowSearchResults] = React.useState(false);

  // Load documents on mount and when projectId changes
  React.useEffect(() => {
    listDocuments(projectId).catch(console.error);
  }, [projectId, listDocuments]);

  const handleDeleteDocument = async (documentId: string) => {
    if (
      window.confirm(
        'Are you sure you want to delete this document? This action cannot be undone.'
      )
    ) {
      try {
        await deleteDocument(documentId);
      } catch (err) {
        console.error('Failed to delete document:', err);
      }
    }
  };

  const handleImportSuccess = () => {
    setIsImportModalOpen(false);
    listDocuments(projectId).catch(console.error);
  };

  const displayedDocuments = showSearchResults ? [] : Array.from(documents.values());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Knowledge Base
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your project documentation and knowledge
          </p>
        </div>
        <Button
          icon={<Plus className="h-5 w-5" />}
          onClick={() => setIsImportModalOpen(true)}
        >
          Import Document
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert type="error" closeable onClose={clearError}>
          {error}
        </Alert>
      )}

      {/* Search Panel */}
      <SearchPanel
        projectId={projectId}
        onSearch={() => setShowSearchResults(true)}
        onClear={() => setShowSearchResults(false)}
      />

      {/* Search Results */}
      {showSearchResults && searchResults.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Search Results for "{currentQuery}"
            </h2>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {searchResults.length} result
              {searchResults.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="grid gap-4">
            {searchResults.map((result) => (
              <Card
                key={result.document_id}
                className="hover:shadow-md transition-shadow"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {result.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {result.source}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                        {(result.relevance_score * 100).toFixed(0)}%
                      </div>
                      <p className="text-xs text-gray-500">Relevance</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                    {result.excerpt}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* No Results State */}
      {showSearchResults && searchResults.length === 0 && !isSearching && (
        <Card className="text-center py-12">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            No documents found matching "{currentQuery}"
          </p>
        </Card>
      )}

      {/* Documents Grid */}
      {!showSearchResults && (
        <div className="space-y-4">
          {displayedDocuments.length > 0 ? (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Documents
                </h2>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {displayedDocuments.length} document
                  {displayedDocuments.length !== 1 ? 's' : ''}
                </span>
              </div>

              <div className="grid gap-4">
                {displayedDocuments.map((doc) => (
                  <DocumentCard
                    key={doc.id}
                    document={doc}
                    onDelete={() => handleDeleteDocument(doc.id)}
                  />
                ))}
              </div>
            </>
          ) : isLoading ? (
            <Card className="text-center py-12">
              <Loader className="h-8 w-8 text-blue-600 dark:text-blue-400 mx-auto mb-4 animate-spin" />
              <p className="text-gray-600 dark:text-gray-400">
                Loading documents...
              </p>
            </Card>
          ) : (
            <Card className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                No documents yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Import your first document to get started
              </p>
              <Button
                variant="secondary"
                size="sm"
                icon={<Plus className="h-4 w-4" />}
                onClick={() => setIsImportModalOpen(true)}
              >
                Import Document
              </Button>
            </Card>
          )}
        </div>
      )}

      {/* Import Modal */}
      <ImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={handleImportSuccess}
        projectId={projectId}
      />
    </div>
  );
};
