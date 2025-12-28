/**
 * BulkImportModal Component
 *
 * Modal for bulk importing multiple documents:
 * - File upload (multiple files, drag & drop)
 * - File validation
 * - Progress tracking
 * - Results display (success/failure)
 */

import React, { useState, useRef } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';

interface BulkImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId?: string;
}

export default function BulkImportModal({ isOpen, onClose, projectId }: BulkImportModalProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const { bulkImportFiles, isBulkOperationLoading, bulkOperationProgress } = useKnowledgeStore();

  const handleFileSelect = (selectedFiles: FileList) => {
    const fileArray = Array.from(selectedFiles);
    setFiles((prev) => [...prev, ...fileArray]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleImport = async () => {
    if (files.length === 0) return;

    try {
      await bulkImportFiles(files, projectId);
      // Files will be cleared when operation completes
      setFiles([]);
    } catch (error) {
      console.error('Bulk import failed:', error);
    }
  };

  const handleClose = () => {
    if (!isBulkOperationLoading) {
      setFiles([]);
      onClose();
    }
  };

  if (!isOpen) return null;

  const isImporting = isBulkOperationLoading && bulkOperationProgress.type === 'import';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-96 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Import Documents</h2>
          <button
            onClick={handleClose}
            disabled={isImporting}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {!isImporting ? (
            <>
              {/* Drag & Drop Area */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragging
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}
              >
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-2"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path d="M32 4v12M26 10h12" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Drag files here or click to browse
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Supports PDF, DOCX, TXT, and other document formats
                </p>
              </div>

              {/* File Input */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={(e) => handleFileSelect(e.target.files!)}
                className="hidden"
                disabled={isImporting}
              />

              {/* File List */}
              {files.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Files to Import ({files.length})</h3>
                  <ul className="space-y-2">
                    {files.map((file, index) => (
                      <li
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded text-sm"
                      >
                        <div className="flex items-center gap-2">
                          <svg className="h-4 w-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6A1 1 0 0118 10V16a2 2 0 01-2 2H4a2 2 0 01-2-2V4z" />
                          </svg>
                          <span className="text-gray-900 dark:text-white truncate">{file.name}</span>
                          <span className="text-xs text-gray-500">({(file.size / 1024).toFixed(1)} KB)</span>
                        </div>
                        <button
                          onClick={() => handleRemoveFile(index)}
                          className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            // Progress View
            <div className="text-center py-8">
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
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Importing {bulkOperationProgress.current} of {bulkOperationProgress.total} files...
              </h3>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.round((bulkOperationProgress.current / bulkOperationProgress.total) * 100)}%`,
                  }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 rounded-b-lg">
          <button
            onClick={handleClose}
            disabled={isImporting}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isImporting ? 'Importing...' : 'Cancel'}
          </button>
          {!isImporting && (
            <button
              onClick={handleImport}
              disabled={files.length === 0}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
            >
              Import {files.length} File{files.length !== 1 ? 's' : ''}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
