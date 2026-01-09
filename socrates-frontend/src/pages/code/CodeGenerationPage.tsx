/**
 * Code Generation Page - AI-powered code generation with Monaco editor
 */

import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { useCodeGenerationStore, useFeatureGate, showError, showSuccess } from '../../stores';
import { apiClient } from '../../api/client';
import type { ProgrammingLanguage } from '../../types/models';
import type { Project } from '../../types/models';

const SUPPORTED_LANGUAGES: { id: ProgrammingLanguage; name: string }[] = [
  { id: 'python', name: 'Python' },
  { id: 'javascript', name: 'JavaScript' },
  { id: 'typescript', name: 'TypeScript' },
  { id: 'java', name: 'Java' },
  { id: 'cpp', name: 'C++' },
  { id: 'csharp', name: 'C#' },
  { id: 'go', name: 'Go' },
  { id: 'rust', name: 'Rust' },
  { id: 'sql', name: 'SQL' },
];

export function CodeGenerationPage() {
  const { projectId: urlProjectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const canGenerateCode = useFeatureGate('code-generation');
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState(urlProjectId || '');
  const [loadingProjects, setLoadingProjects] = useState(true);

  const {
    currentCode,
    generatedCode,
    validationResult,
    currentLanguage,
    isLoading,
    error,
    generateCode,
    validateCode,
    setCurrentCode,
    setCurrentLanguage,
    clearError,
  } = useCodeGenerationStore();

  const [specification, setSpecification] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const editorRef = useRef(null);

  // Load projects on mount
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await apiClient.get('/projects') as any;
        const projectList = response?.data || response || [];
        setProjects(Array.isArray(projectList) ? projectList : []);
        
        // Set selected project from URL or default to first project
        if (urlProjectId && projectList.some((p: Project) => p.project_id === urlProjectId)) {
          setSelectedProjectId(urlProjectId);
        } else if (projectList.length > 0) {
          setSelectedProjectId(projectList[0].project_id);
        }
      } catch (err) {
        console.error('Failed to load projects:', err);
        setProjects([]);
      } finally {
        setLoadingProjects(false);
      }
    };

    loadProjects();
  }, [urlProjectId]);

  const handleProjectChange = (projectId: string) => {
    setSelectedProjectId(projectId);
    navigate(`/code/${projectId}`);
  };

  const projectId = selectedProjectId || urlProjectId;

  if (!canGenerateCode) {
    return (
      <div className="p-8">
        <div className="max-w-2xl mx-auto">
          <div className="card bg-yellow-50 border border-yellow-200">
            <h2 className="text-xl font-bold text-yellow-900 mb-2">Pro Feature Required</h2>
            <p className="text-yellow-800">
              Code generation is available on the Pro plan and above. Upgrade your account to access this feature.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleGenerateCode = async () => {
    if (!projectId || !specification.trim()) {
      showError('Error', 'Please select a project and enter a specification');
      return;
    }

    try {
      await generateCode(projectId, specification, currentLanguage);
      showSuccess('Success', 'Code generated successfully');
    } catch (err) {
      showError('Generation Failed', err instanceof Error ? err.message : 'Failed to generate code');
    }
  };

  const handleValidateCode = async () => {
    if (!projectId) return;

    try {
      await validateCode(projectId, currentCode, currentLanguage);
      if (validationResult?.is_valid) {
        showSuccess('Valid', 'Code validation passed');
      }
    } catch (err) {
      showError('Validation Failed', err instanceof Error ? err.message : 'Failed to validate code');
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Code Generation</h1>
        <p className="text-gray-600">Generate, validate, and refactor code with AI assistance</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Panel - Controls */}
        <div className="lg:col-span-1 space-y-6">
          {/* Project Selector */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Project</h3>
            {loadingProjects ? (
              <div className="text-gray-500 text-sm">Loading projects...</div>
            ) : projects.length === 0 ? (
              <div className="text-gray-500 text-sm">No projects available</div>
            ) : (
              <select
                value={selectedProjectId}
                onChange={(e) => handleProjectChange(e.target.value)}
                className="input-field"
              >
                <option value="">Select a project</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Language Selector */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Language</h3>
            <select
              value={currentLanguage}
              onChange={(e) => setCurrentLanguage(e.target.value as ProgrammingLanguage)}
              className="input-field"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          {/* Specification Input */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Specification</h3>
            <textarea
              value={specification}
              onChange={(e) => setSpecification(e.target.value)}
              placeholder="Describe what code you want to generate..."
              rows={6}
              className="input-field resize-none"
              disabled={isLoading}
            />
            <button
              onClick={handleGenerateCode}
              disabled={isLoading || !specification.trim()}
              className="btn-primary w-full mt-4 disabled:opacity-50"
            >
              {isLoading ? 'Generating...' : 'Generate Code'}
            </button>
          </div>

          {/* Code Info */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Code Info</h3>
            <div className="space-y-2 text-sm">
              <p className="text-gray-600">
                Language: <span className="font-semibold">{currentLanguage}</span>
              </p>
              <p className="text-gray-600">
                Lines: <span className="font-semibold">{currentCode.split('\n').length}</span>
              </p>
              {generatedCode?.token_usage && (
                <p className="text-gray-600">
                  Tokens: <span className="font-semibold">{generatedCode.token_usage}</span>
                </p>
              )}
            </div>
          </div>

          {/* Validation Results */}
          {validationResult && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Validation</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <span className={`w-3 h-3 rounded-full ${validationResult.is_valid ? 'bg-green-500' : 'bg-red-500'}`}></span>
                  <span className="font-semibold">
                    {validationResult.is_valid ? 'Valid' : 'Invalid'}
                  </span>
                </div>

                {validationResult.errors.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-red-600 mb-1">Errors:</p>
                    <ul className="text-xs text-red-700 space-y-1">
                      {validationResult.errors.map((err, i) => (
                        <li key={`error-${i}-${err.substring(0, 20)}`}>• {err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {validationResult.warnings.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-yellow-600 mb-1">Warnings:</p>
                    <ul className="text-xs text-yellow-700 space-y-1">
                      {validationResult.warnings.map((warn, i) => (
                        <li key={`warning-${i}-${warn.substring(0, 20)}`}>• {warn}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <button
                  onClick={handleValidateCode}
                  disabled={isLoading}
                  className="btn-secondary w-full text-sm"
                >
                  Re-validate
                </button>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="card bg-red-50 border border-red-200">
              <p className="text-red-800 text-sm mb-2">{error}</p>
              <button onClick={clearError} className="text-red-600 text-sm font-semibold">
                Dismiss
              </button>
            </div>
          )}
        </div>

        {/* Right Panel - Editor */}
        <div className="lg:col-span-2">
          <div className="card h-full" style={{ minHeight: '600px' }}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Code Editor</h3>
              <div className="flex space-x-2">
                <button
                  onClick={handleValidateCode}
                  disabled={isLoading || !currentCode.trim()}
                  className="btn-secondary text-sm disabled:opacity-50"
                >
                  Validate
                </button>
                <button
                  onClick={() => setCurrentCode('')}
                  className="btn-secondary text-sm"
                >
                  Clear
                </button>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="btn-secondary text-sm"
                >
                  {showHistory ? 'Hide' : 'Show'} History
                </button>
              </div>
            </div>

            {/* Monaco Editor */}
            <div style={{ height: '500px', marginBottom: '16px' }}>
              <Editor
                height="100%"
                language={currentLanguage === 'cpp' ? 'cpp' : currentLanguage}
                value={currentCode}
                onChange={(value) => setCurrentCode(value || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  fontFamily: "'Fira Code', 'Courier New', monospace",
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  tabSize: 2,
                }}
                theme="vs-light"
              />
            </div>

            {/* Generated Code Info */}
            {generatedCode && (
              <div className="pt-4 border-t">
                <h4 className="font-semibold mb-2">Generation Details</h4>
                <p className="text-sm text-gray-600 mb-2">{generatedCode.explanation}</p>
                <p className="text-xs text-gray-500">
                  Generated at: {new Date(generatedCode.created_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
