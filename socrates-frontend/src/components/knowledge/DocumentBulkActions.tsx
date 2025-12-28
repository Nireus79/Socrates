/**
 * DocumentBulkActions Component
 *
 * Toolbar for bulk document operations:
 * - Select all / deselect all
 * - Bulk delete with confirmation
 * - Bulk import trigger
 * - Selection counter
 */

import React, { useState } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';

interface DocumentBulkActionsProps {
  selectedCount: number;
  totalCount: number;
  onBulkImportClick: () => void;
  projectId?: string;
}

export default function DocumentBulkActions({
  selectedCount,
  totalCount,
  onBulkImportClick,
  projectId,
}: DocumentBulkActionsProps) {
  const { selectAll, unselectAll, bulkDeleteSelected, isBulkOperationLoading } = useKnowledgeStore();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleBulkDelete = async () => {
    setIsDeleting(true);
    try {
      await bulkDeleteSelected(projectId);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Bulk delete failed:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const hasSelection = selectedCount > 0;

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
        {/* Left: Selection Info */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="select-all"
              checked={selectedCount > 0 && selectedCount === totalCount}
              indeterminate={selectedCount > 0 && selectedCount < totalCount}
              onChange={(e) => {
                if (e.target.checked) {
                  selectAll();
                } else {
                  unselectAll();
                }
              }}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 cursor-pointer w-5 h-5"
            />
            <label htmlFor="select-all" className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">
              Select All
            </label>
          </div>

          {hasSelection && (
            <div className="text-sm text-gray-600 dark:text-gray-400 px-3 py-1 bg-blue-50 dark:bg-blue-900 rounded">
              {selectedCount} of {totalCount} selected
            </div>
          )}
        </div>

        {/* Right: Action Buttons */}
        <div className="flex items-center gap-2">
          {hasSelection && (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={isBulkOperationLoading || isDeleting}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete Selected
            </button>
          )}

          <button
            onClick={onBulkImportClick}
            disabled={isBulkOperationLoading}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 dark:bg-blue-700 hover:bg-blue-700 dark:hover:bg-blue-600 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Import Files
          </button>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900">
              <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white text-center mb-2">Delete Documents</h3>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to delete {selectedCount} document{selectedCount !== 1 ? 's' : ''}? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded transition-colors disabled:bg-red-400 disabled:cursor-not-allowed"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
