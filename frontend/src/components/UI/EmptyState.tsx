/**
 * 빈 상태 컴포넌트
 */
import React from 'react';

interface EmptyStateProps {
  /** 아이콘 */
  icon?: string;
  /** 제목 */
  title: string;
  /** 설명 */
  description?: string;
  /** 액션 버튼 */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** 크기 */
  size?: 'small' | 'medium' | 'large';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = '📊',
  title,
  description,
  action,
  size = 'medium'
}) => {
  const sizeClasses = {
    small: 'empty-state-small',
    medium: 'empty-state-medium',
    large: 'empty-state-large'
  };

  return (
    <div className={`empty-state ${sizeClasses[size]}`}>
      <div className="empty-content">
        <div className="empty-icon">{icon}</div>
        <h3 className="empty-title">{title}</h3>
        {description && <p className="empty-description">{description}</p>}
        {action && (
          <button onClick={action.onClick} className="btn btn-primary">
            {action.label}
          </button>
        )}
      </div>
      
      <style>{`
        .empty-state {
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--color-bg-secondary);
          border: 2px dashed var(--color-border);
          border-radius: 12px;
          text-align: center;
        }
        
        .empty-state-small {
          padding: 30px 20px;
        }
        
        .empty-state-medium {
          padding: 60px 20px;
        }
        
        .empty-state-large {
          padding: 80px 20px;
        }
        
        .empty-content {
          max-width: 400px;
        }
        
        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }
        
        .empty-state-small .empty-icon {
          font-size: 32px;
          margin-bottom: 12px;
        }
        
        .empty-state-large .empty-icon {
          font-size: 64px;
          margin-bottom: 20px;
        }
        
        .empty-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--color-text);
          margin: 0 0 8px 0;
        }
        
        .empty-state-small .empty-title {
          font-size: 16px;
        }
        
        .empty-state-large .empty-title {
          font-size: 20px;
        }
        
        .empty-description {
          color: var(--color-text-secondary);
          margin: 0 0 20px 0;
          line-height: 1.5;
          font-size: 14px;
        }
        
        .empty-state-small .empty-description {
          font-size: 13px;
          margin-bottom: 16px;
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
      `}</style>
    </div>
  );
};