/**
 * 에러 바운더리 컴포넌트
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <div className="error-content">
            <div className="error-icon">⚠️</div>
            <h2>문제가 발생했습니다</h2>
            <p>예상치 못한 오류가 발생했습니다. 페이지를 새로고침하거나 다시 시도해주세요.</p>
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-details">
                <summary>기술적 세부사항</summary>
                <pre className="error-stack">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            
            <div className="error-actions">
              <button onClick={this.handleRetry} className="btn btn-primary">
                다시 시도
              </button>
              <button onClick={() => window.location.reload()} className="btn btn-secondary">
                페이지 새로고침
              </button>
            </div>
          </div>
          
          <style>{`
            .error-boundary {
              display: flex;
              align-items: center;
              justify-content: center;
              min-height: 400px;
              padding: 40px 20px;
              background: var(--color-bg-secondary);
              border: 1px solid var(--color-border);
              border-radius: 12px;
              margin: 20px 0;
            }
            
            .error-content {
              text-align: center;
              max-width: 500px;
            }
            
            .error-icon {
              font-size: 48px;
              margin-bottom: 16px;
            }
            
            .error-content h2 {
              font-size: 24px;
              margin-bottom: 12px;
              color: var(--color-text);
            }
            
            .error-content p {
              color: var(--color-text-secondary);
              margin-bottom: 24px;
              line-height: 1.6;
            }
            
            .error-details {
              text-align: left;
              margin: 20px 0;
              padding: 16px;
              background: var(--color-bg);
              border: 1px solid var(--color-border);
              border-radius: 8px;
            }
            
            .error-details summary {
              cursor: pointer;
              font-weight: 600;
              color: var(--color-text-secondary);
              margin-bottom: 12px;
            }
            
            .error-stack {
              font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
              font-size: 12px;
              color: var(--color-danger);
              white-space: pre-wrap;
              overflow-x: auto;
            }
            
            .error-actions {
              display: flex;
              gap: 12px;
              justify-content: center;
              flex-wrap: wrap;
            }
            
            .btn {
              padding: 10px 20px;
              border: none;
              border-radius: 6px;
              font-size: 14px;
              font-weight: 600;
              cursor: pointer;
              transition: all 0.2s;
            }
            
            .btn-primary {
              background: var(--color-primary);
              color: white;
            }
            
            .btn-primary:hover {
              background: #0969da;
            }
            
            .btn-secondary {
              background: var(--color-bg);
              color: var(--color-text);
              border: 1px solid var(--color-border);
            }
            
            .btn-secondary:hover {
              background: var(--color-bg-tertiary);
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}