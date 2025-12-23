/**
 * ErrorBoundary Component - Catch React errors and display fallback UI
 */

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './interactive/Button';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  static displayName = 'ErrorBoundary';

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 p-4">
          <div className="max-w-md w-full space-y-6">
            {/* Error Icon */}
            <div className="flex justify-center">
              <AlertTriangle className="h-16 w-16 text-red-600 dark:text-red-400" />
            </div>

            {/* Error Content */}
            <div className="space-y-2 text-center">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Something Went Wrong
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                An unexpected error occurred. Please try again or contact support if the problem persists.
              </p>
            </div>

            {/* Error Details (Dev Only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="p-4 bg-red-50 dark:bg-red-900 rounded-lg border border-red-200 dark:border-red-800">
                <p className="text-xs font-mono text-red-800 dark:text-red-200 whitespace-pre-wrap break-words">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-3">
              <Button
                variant="primary"
                fullWidth
                icon={<RefreshCw className="h-4 w-4" />}
                onClick={this.handleReset}
              >
                Try Again
              </Button>

              <Button
                variant="secondary"
                fullWidth
                onClick={() => (window.location.href = '/dashboard')}
              >
                Go to Dashboard
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
