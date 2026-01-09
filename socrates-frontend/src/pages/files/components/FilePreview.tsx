/**
 * FilePreview Component - Display code with Monaco Editor
 */

import React, { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { useParams } from 'react-router-dom';
import { apiClient } from '../../../api/client';
import type { FileNode } from '../../../stores/projectStore';

interface FilePreviewProps {
  file: FileNode | null;
  content: string;
}

const languageMap: Record<string, string> = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  tsx: 'typescript',
  jsx: 'javascript',
  java: 'java',
  cs: 'csharp',
  csharp: 'csharp',
  cpp: 'cpp',
  c: 'c',
  go: 'go',
  rust: 'rust',
  sql: 'sql',
  txt: 'text',
  md: 'markdown',
  json: 'json',
  yaml: 'yaml',
  yml: 'yaml',
};

const getMonacoLanguage = (language?: string): string => {
  if (!language) return 'text';
  return languageMap[language.toLowerCase()] || language;
};

export const FilePreview: React.FC<FilePreviewProps> = ({ file, content }) => {
  const { projectId } = useParams<{ projectId: string }>();
  const [editorHeight, setEditorHeight] = useState('600px');
  const [isMounted, setIsMounted] = useState(false);
  const [loadedContent, setLoadedContent] = useState(content);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
    // Adjust height on mount
    const adjustHeight = () => {
      const windowHeight = window.innerHeight;
      const headerHeight = 180; // Approximate height of header and other elements
      setEditorHeight(`${Math.max(400, windowHeight - headerHeight)}px`);
    };

    adjustHeight();
    window.addEventListener('resize', adjustHeight);
    return () => window.removeEventListener('resize', adjustHeight);
  }, []);

  // Try to fetch file content if not provided
  useEffect(() => {
    if (!content && file && projectId) {
      setIsLoadingContent(true);
      setLoadError(null);

      apiClient
        .get(`/projects/${projectId}/files/content?file_name=${file.name}`)
        .then((response: any) => {
          if (response.data?.content) {
            setLoadedContent(response.data.content);
          } else {
            setLoadError('Could not load file content');
          }
        })
        .catch((error) => {
          console.error('Error loading file content:', error);
          // Fallback: if API doesn't have the endpoint, show what we have
          if (content) {
            setLoadedContent(content);
          } else {
            setLoadError('Unable to load file content');
          }
        })
        .finally(() => {
          setIsLoadingContent(false);
        });
    } else if (content) {
      setLoadedContent(content);
    }
  }, [file, content, projectId]);

  if (!file) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
        <p className="text-gray-500 dark:text-gray-400">Select a file to view its content</p>
      </div>
    );
  }

  if (isLoadingContent) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
        <p className="text-gray-500 dark:text-gray-400">Loading content...</p>
      </div>
    );
  }

  if (loadError || (!loadedContent && !content)) {
    return (
      <div className="h-full flex items-center justify-center bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
        <p className="text-gray-500 dark:text-gray-400">{loadError || 'Content not available for this file'}</p>
      </div>
    );
  }

  const monacoLanguage = getMonacoLanguage(file.language);

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
      {/* Editor Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">{file.name}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Language: <span className="capitalize">{file.language || 'Unknown'}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 overflow-hidden">
        {isMounted && (
          <Editor
            height={editorHeight}
            language={monacoLanguage}
            value={loadedContent || ''}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              lineNumbers: 'on',
              wordWrap: 'on',
              scrollBeyondLastLine: false,
              fontFamily: 'Monaco, Menlo, Consolas, monospace',
              fontSize: 13,
              lineHeight: 1.6,
            }}
            theme="vs-dark"
          />
        )}
      </div>
    </div>
  );
};

export default FilePreview;
