/**
 * FileUpload Component - File input with drag & drop support
 */

import React from 'react';
import { Upload, File, X } from 'lucide-react';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in bytes
  label?: string;
  help?: string;
  disabled?: boolean;
  selectedFiles?: File[];
  onRemoveFile?: (index: number) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  accept = '*/*',
  multiple = false,
  maxSize,
  label = 'Upload files',
  help = 'Drag and drop files here or click to browse',
  disabled = false,
  selectedFiles = [],
  onRemoveFile,
}) => {
  const [isDragActive, setIsDragActive] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragActive(e.type === 'dragenter' || e.type === 'dragover');
    }
  };

  const validateFiles = (files: FileList | null): File[] => {
    if (!files) return [];

    const validFiles: File[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (maxSize && file.size > maxSize) {
        console.warn(`File ${file.name} exceeds max size of ${maxSize} bytes`);
        continue;
      }
      validFiles.push(file);
    }
    return validFiles;
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (disabled) return;

    const files = validateFiles(e.dataTransfer.files);
    const filesToAdd = multiple ? files : files.slice(0, 1);
    if (filesToAdd.length > 0) {
      onFilesSelected(filesToAdd);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = validateFiles(e.target.files);
    const filesToAdd = multiple ? files : files.slice(0, 1);
    if (filesToAdd.length > 0) {
      onFilesSelected(filesToAdd);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="w-full space-y-2">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleChange}
          disabled={disabled}
          className="hidden"
        />

        <Upload className="mx-auto h-10 w-10 text-gray-400 dark:text-gray-500 mb-2" />
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
          Click to upload or drag and drop
        </p>
        {help && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {help}
          </p>
        )}
        {maxSize && (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Max file size: {(maxSize / 1024 / 1024).toFixed(2)}MB
          </p>
        )}
      </div>

      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          {selectedFiles.map((file, index) => (
            <div
              key={`${file.name}-${index}`}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center gap-2 min-w-0">
                <File className="h-4 w-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {(file.size / 1024).toFixed(2)}KB
                  </p>
                </div>
              </div>
              {onRemoveFile && (
                <button
                  onClick={() => onRemoveFile(index)}
                  className="ml-2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex-shrink-0"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

FileUpload.displayName = 'FileUpload';
