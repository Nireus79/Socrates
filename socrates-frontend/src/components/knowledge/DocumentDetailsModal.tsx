/**
 * DocumentDetailsModal Component
 *
 * Displays detailed information about a document:
 * - Full metadata (title, source, type, upload date)
 * - Content preview (first 500 characters)
 * - Analytics (views, word count, reading time)
 * - Word count and character count
 * - Download and delete actions
 */

import React, { useEffect, useState } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import type { DocumentDetails, DocumentAnalytics } from '../../types/models';

interface DocumentDetailsModalProps {
  documentId: string;
  isOpen: boolean;
  onClose: () => void;
  onDelete?: () => void;
}

export default function DocumentDetailsModal({
  documentId,
  isOpen,
  onClose,
  onDelete,
}: DocumentDetailsModalProps) {
  const { loadDocumentDetails, loadDocumentAnalytics } = useKnowledgeStore();
  const [details, setDetails] = useState<DocumentDetails | null>(null);
  const [analytics, setAnalytics] = useState<DocumentAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'analytics'>('details');

  useEffect(() => {
    if (!isOpen || !documentId) return;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [detailsData, analyticsData] = await Promise.all([
          loadDocumentDetails(documentId),
          loadDocumentAnalytics(documentId),
        ]);

        setDetails(detailsData);
        setAnalytics(analyticsData);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load document details';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [isOpen, documentId, loadDocumentDetails, loadDocumentAnalytics]);

  if (!isOpen) return null;

  const getDocumentTypeColor = (type: string) => {
    switch (type) {
      case 'text':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'file':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'url':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-96 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
            {details?.title || 'Document Details'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-48">
              <div className="text-center">
                <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900 mb-4">
                  <svg className="h-6 w-6 text-blue-600 dark:text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                </div>
                <p className="text-gray-600 dark:text-gray-400">Loading details...</p>
              </div>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          ) : details ? (
            <div className="space-y-6">
              {/* Tabs */}
              <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => setActiveTab('details')}
                  className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                    activeTab === 'details'
                      ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300'
                  }`}
                >
                  Details
                </button>
                <button
                  onClick={() => setActiveTab('analytics')}
                  className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                    activeTab === 'analytics'
                      ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300'
                  }`}
                >
                  Analytics
                </button>
              </div>

              {/* Details Tab */}
              {activeTab === 'details' && (
                <div className="space-y-4">
                  {/* Metadata */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Type
                      </p>
                      <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getDocumentTypeColor(details.document_type)}`}>
                        {details.document_type}
                      </span>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Uploaded
                      </p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {formatDate(details.uploaded_at)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Word Count
                      </p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {details.word_count?.toLocaleString() || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Characters
                      </p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {details.character_count?.toLocaleString() || 0}
                      </p>
                    </div>
                  </div>

                  {/* Source */}
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
                      Source
                    </p>
                    <p className="text-sm text-gray-900 dark:text-white break-all truncate">
                      {details.source}
                    </p>
                  </div>

                  {/* Preview */}
                  {details.preview && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
                        Preview
                      </p>
                      <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-4">
                          {details.preview}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Analytics Tab */}
              {activeTab === 'analytics' && analytics && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-blue-50 dark:bg-blue-900 rounded-lg">
                      <p className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase mb-1">
                        Views
                      </p>
                      <p className="text-2xl font-bold text-blue-900 dark:text-blue-200">
                        {analytics.views || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-green-50 dark:bg-green-900 rounded-lg">
                      <p className="text-xs font-medium text-green-600 dark:text-green-400 uppercase mb-1">
                        Searches
                      </p>
                      <p className="text-2xl font-bold text-green-900 dark:text-green-200">
                        {analytics.searches || 0}
                      </p>
                    </div>
                  </div>

                  {analytics.estimated_reading_time_minutes && (
                    <div className="p-4 bg-orange-50 dark:bg-orange-900 rounded-lg">
                      <p className="text-xs font-medium text-orange-600 dark:text-orange-400 uppercase mb-1">
                        Estimated Reading Time
                      </p>
                      <p className="text-lg font-semibold text-orange-900 dark:text-orange-200">
                        ~{analytics.estimated_reading_time_minutes} minutes
                      </p>
                    </div>
                  )}

                  {analytics.last_accessed && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase mb-1">
                        Last Accessed
                      </p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {formatDate(analytics.last_accessed)}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 rounded-b-lg">
          {onDelete && (
            <button
              onClick={() => {
                onDelete();
                onClose();
              }}
              className="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900 rounded transition-colors"
            >
              Delete
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
