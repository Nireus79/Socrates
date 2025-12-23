/**
 * Import Modal - Multi-step document import wizard
 *
 * Supports:
 * - File upload
 * - URL import
 * - Pasted text
 */

import React from 'react';
import { Upload, Link, Type, AlertCircle, CheckCircle } from 'lucide-react';
import { useKnowledgeStore } from '../../stores';
import { Modal } from '../common';
import { Button } from '../common';
import { Input } from '../common';
import { Card } from '../common';
import { TextArea } from '../common';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  projectId?: string;
}

type ImportType = 'file' | 'url' | 'text';

export const ImportModal: React.FC<ImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  projectId,
}) => {
  const { importFile, importURL, importText, isImporting, error } =
    useKnowledgeStore();

  const [importType, setImportType] = React.useState<ImportType>('file');
  const [file, setFile] = React.useState<File | null>(null);
  const [url, setUrl] = React.useState('');
  const [textTitle, setTextTitle] = React.useState('');
  const [textContent, setTextContent] = React.useState('');
  const [validationError, setValidationError] = React.useState<string | null>(
    null
  );
  const [isSuccess, setIsSuccess] = React.useState(false);

  const handleImport = async () => {
    setValidationError(null);

    try {
      if (importType === 'file') {
        if (!file) {
          setValidationError('Please select a file');
          return;
        }
        await importFile(file, projectId);
      } else if (importType === 'url') {
        if (!url.trim()) {
          setValidationError('Please enter a URL');
          return;
        }
        if (!url.includes('://')) {
          setValidationError('Please enter a valid URL (e.g., https://...)');
          return;
        }
        await importURL(url.trim(), projectId);
      } else if (importType === 'text') {
        if (!textTitle.trim()) {
          setValidationError('Please enter a title');
          return;
        }
        if (!textContent.trim()) {
          setValidationError('Please enter content');
          return;
        }
        await importText(textTitle.trim(), textContent.trim(), projectId);
      }

      setIsSuccess(true);
      setTimeout(() => {
        resetForm();
        onClose();
        onSuccess?.();
      }, 1500);
    } catch (err) {
      console.error('Import failed:', err);
    }
  };

  const resetForm = () => {
    setImportType('file');
    setFile(null);
    setUrl('');
    setTextTitle('');
    setTextContent('');
    setValidationError(null);
    setIsSuccess(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Import Document"
      size="md"
    >
      {isSuccess ? (
        <div className="text-center py-8">
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Import Successful
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Document has been added to your knowledge base
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Error Alert */}
          {(validationError || error) && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700 dark:text-red-300">
                {validationError || error}
              </p>
            </div>
          )}

          {/* Import Type Selector */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-900 dark:text-white">
              Import Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setImportType('file')}
                className={`p-3 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
                  importType === 'file'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Upload className="h-5 w-5" />
                <span className="text-xs font-medium">File</span>
              </button>
              <button
                type="button"
                onClick={() => setImportType('url')}
                className={`p-3 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
                  importType === 'url'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Link className="h-5 w-5" />
                <span className="text-xs font-medium">URL</span>
              </button>
              <button
                type="button"
                onClick={() => setImportType('text')}
                className={`p-3 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${
                  importType === 'text'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Type className="h-5 w-5" />
                <span className="text-xs font-medium">Text</span>
              </button>
            </div>
          </div>

          {/* File Upload */}
          {importType === 'file' && (
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                Select File
              </label>
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="file-input"
                  accept=".pdf,.txt,.docx,.md"
                  disabled={isImporting}
                />
                <label htmlFor="file-input" className="cursor-pointer">
                  <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {file ? file.name : 'Drop file or click to select'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    PDF, TXT, DOCX, or MD files
                  </p>
                </label>
              </div>
            </div>
          )}

          {/* URL Import */}
          {importType === 'url' && (
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                URL
              </label>
              <Input
                type="url"
                placeholder="https://example.com/article"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isImporting}
                icon={<Link className="h-4 w-4" />}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Content from this URL will be imported and indexed
              </p>
            </div>
          )}

          {/* Text Import */}
          {importType === 'text' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Title
                </label>
                <Input
                  type="text"
                  placeholder="Document title"
                  value={textTitle}
                  onChange={(e) => setTextTitle(e.target.value)}
                  disabled={isImporting}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Content
                </label>
                <TextArea
                  placeholder="Paste your text content here..."
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  disabled={isImporting}
                  rows={6}
                />
              </div>
            </div>
          )}

          {/* Info Box */}
          <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <p className="font-medium mb-2">What happens next:</p>
              <ul className="list-disc pl-5 space-y-1 text-xs">
                <li>Document will be processed and indexed</li>
                <li>Content will be split into chunks</li>
                <li>Searchable embeddings will be generated</li>
                <li>You'll be able to search and reference it</li>
              </ul>
            </div>
          </Card>
        </div>
      )}

      {/* Action Buttons */}
      {!isSuccess && (
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-800 mt-4">
          <Button
            variant="secondary"
            onClick={handleClose}
            disabled={isImporting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleImport}
            isLoading={isImporting}
          >
            Import
          </Button>
        </div>
      )}
      {isSuccess && (
        <div className="flex justify-center pt-4 border-t border-gray-200 dark:border-gray-800 mt-4">
          <Button
            variant="primary"
            onClick={handleClose}
          >
            Done
          </Button>
        </div>
      )}
    </Modal>
  );
};
