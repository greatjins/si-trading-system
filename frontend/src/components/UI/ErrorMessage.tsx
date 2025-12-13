/**
 * 에러 메시지 컴포넌트
 */
import React from 'react';

interface ErrorMessageProps {
  /** 에러 메시지 */
  message: string;
  /** 에러 제목 */
  title?: string;
  /** 재시도 버튼 표시 여부 */
  showRetry?: boolean;
  /** 재시도 핸들러 */
  onRetry?: () => void;
  /** 에러 타입 */
  type?: 'error' | 'warning' | 'info';
  /** 상세 에러 정보 (개발 모드에서만 표시) */
  details?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  title,
  showRetry = false,
  onRetry,
  type = 'error',
  details
}) => {
  const icons = {
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const messageClass = `message message-${type}`;

  return (
    <div className={messageClass}>
      <div className="d-flex align-items-start gap-3">
        <span className="text-lg">{icons[type]}</span>
        <div className="flex-1">
          {title && <h3 className="font-weight-medium mb-1">{title}</h3>}
          <p className="mb-0">{message}</p>
          
          {process.env.NODE_ENV === 'development' && details && (
            <details className="mt-3">
              <summary className="font-weight-medium text-sm cursor-pointer">기술적 세부사항</summary>
              <pre className="text-xs mt-2 p-2" style={{ 
                fontFamily: 'monospace', 
                background: 'var(--color-background)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                whiteSpace: 'pre-wrap',
                overflowX: 'auto'
              }}>
                {details}
              </pre>
            </details>
          )}
          
          {showRetry && onRetry && (
            <div className="mt-3">
              <button onClick={onRetry} className="btn btn-primary btn-sm">
                다시 시도
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};