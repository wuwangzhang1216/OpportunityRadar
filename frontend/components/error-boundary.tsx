"use client";

import React from "react";
import { motion } from "framer-motion";
import { AlertTriangle, RefreshCw, Home, Bug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    this.props.onError?.(error, errorInfo);

    // Log to console in development
    if (process.env.NODE_ENV === "development") {
      console.error("Error Boundary caught an error:", error);
      console.error("Component stack:", errorInfo.componentStack);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onRetry={this.handleRetry}
        />
      );
    }

    return this.props.children;
  }
}

interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  onRetry?: () => void;
}

export function ErrorFallback({ error, errorInfo, onRetry }: ErrorFallbackProps) {
  const isDev = process.env.NODE_ENV === "development";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="min-h-[400px] flex items-center justify-center p-6"
    >
      <Card className="max-w-lg w-full">
        <CardContent className="pt-6 text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", bounce: 0.5 }}
            className="mb-6"
          >
            <div className="h-16 w-16 rounded-2xl bg-urgency-warning/10 flex items-center justify-center mx-auto">
              <AlertTriangle className="h-8 w-8 text-urgency-warning" />
            </div>
          </motion.div>

          <h2 className="text-xl font-bold text-foreground mb-2">
            Something went wrong
          </h2>
          <p className="text-muted-foreground mb-6">
            We encountered an unexpected error. Please try again or return to the dashboard.
          </p>

          {isDev && error && (
            <div className="mb-6 text-left">
              <details className="bg-secondary/50 rounded-lg p-4">
                <summary className="text-sm font-medium text-foreground cursor-pointer flex items-center gap-2">
                  <Bug className="h-4 w-4" />
                  Error Details (Dev Mode)
                </summary>
                <div className="mt-3 space-y-3">
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Error Message:</p>
                    <code className="text-xs text-urgency-critical bg-urgency-critical/10 p-2 rounded block overflow-auto">
                      {error.message}
                    </code>
                  </div>
                  {errorInfo?.componentStack && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">Component Stack:</p>
                      <pre className="text-xs text-muted-foreground bg-secondary p-2 rounded overflow-auto max-h-32">
                        {errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {onRetry && (
              <Button onClick={onRetry} variant="default" className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Try Again
              </Button>
            )}
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => window.location.href = "/dashboard"}
            >
              <Home className="h-4 w-4" />
              Back to Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Hook-based error boundary wrapper for functional components
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: React.ReactNode
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}

// Query Error Fallback (for React Query errors)
interface QueryErrorFallbackProps {
  error: Error;
  resetErrorBoundary?: () => void;
  title?: string;
  description?: string;
}

export function QueryErrorFallback({
  error,
  resetErrorBoundary,
  title = "Failed to load data",
  description = "There was an error loading the data. Please try again.",
}: QueryErrorFallbackProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-urgency-critical/20 bg-urgency-critical/5 p-6 text-center"
    >
      <AlertTriangle className="h-8 w-8 text-urgency-critical mx-auto mb-3" />
      <h3 className="font-semibold text-foreground mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground mb-4">{description}</p>
      {process.env.NODE_ENV === "development" && (
        <p className="text-xs text-urgency-critical mb-4 font-mono">
          {error.message}
        </p>
      )}
      {resetErrorBoundary && (
        <Button size="sm" onClick={resetErrorBoundary} className="gap-2">
          <RefreshCw className="h-3 w-3" />
          Retry
        </Button>
      )}
    </motion.div>
  );
}
