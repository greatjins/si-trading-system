/**
 * 로딩 스피너 컴포넌트
 */
import React from 'react';

interface LoadingSpinnerProps {
  /** 로딩 메시지 */
  message?: string;
  /** 크기 */
  size?: 'small' | 'medium' | 'large';
  /** 전체 화면 오버레이 여부 */
  overlay?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = '로딩 중...',
  size = 'medium',
  overlay = false
}) => {
  const sizeClasses = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large'
  };

  const content = (
    <div className={`loading-spinner-container ${overlay ? 'overlay' : ''}`}>
      <div className={`loading-spinner ${sizeClasses[size]}`}></div>
      {message && <p className="loading-message">{message}</p>}
      
      <style>{`
        .loading-spinner-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px 20px;
        }
        
        .loading-spinner-container.overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(255, 255, 255, 0.9);
          z-index: 9999;
          backdrop-filter: blur(2px);
        }
        
        .loading-spinner {
          border: 4px solid var(--color-bg-secondary);
          border-top: 4px solid var(--color-primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }
        
        .spinner-small {
          width: 24px;
          height: 24px;
          border-width: 2px;
        }
        
        .spinner-medium {
          width: 40px;
          height: 40px;
          border-width: 4px;
        }
        
        .spinner-large {
          width: 60px;
          height: 60px;
          border-width: 6px;
        }
        
        .loading-message {
          color: var(--color-text-secondary);
          font-size: 14px;
          margin: 0;
          text-align: center;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @media (prefers-color-scheme: dark) {
          .loading-spinner-container.overlay {
            background: rgba(13, 17, 23, 0.9);
          }
        }
      `}</style>
    </div>
  );

  return content;
};