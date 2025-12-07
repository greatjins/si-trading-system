/**
 * 전략 목록 페이지
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '../components/Layout/PageLayout';
import { httpClient } from '../services/http';

interface Strategy {
  strategy_id: number;
  name: string;
  description: string;
  created_at: string;
}

export default function StrategyListPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await httpClient.get('/api/strategy-builder/list');
      setStrategies(response.data);
    } catch (error) {
      console.error('전략 목록 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (strategyId: number) => {
    navigate(`/strategy-builder?edit=${strategyId}`);
  };

  const handleDelete = async (strategyId: number, name: string) => {
    if (!confirm(`"${name}" 전략을 삭제하시겠습니까?`)) return;

    try {
      await httpClient.delete(`/api/strategy-builder/${strategyId}`);
      alert('전략이 삭제되었습니다');
      loadStrategies();
    } catch (error) {
      console.error('전략 삭제 실패:', error);
      alert('전략 삭제에 실패했습니다');
    }
  };

  const handleBacktest = (_strategyId: number, name: string) => {
    navigate(`/backtest?strategy=${encodeURIComponent(name)}`);
  };

  if (loading) {
    return (
      <PageLayout title="내 전략">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title="내 전략" description="저장된 전략을 관리합니다">
      <div className="strategy-list-page">
        <div className="page-header-actions">
          <button onClick={() => navigate('/strategy-builder')} className="btn btn-primary">
            + 새 전략 만들기
          </button>
        </div>

        {strategies.length === 0 ? (
          <div className="empty-state">
            <p>저장된 전략이 없습니다</p>
            <button onClick={() => navigate('/strategy-builder')} className="btn btn-primary">
              첫 전략 만들기
            </button>
          </div>
        ) : (
          <div className="strategies-grid">
            {strategies.map((strategy) => (
              <div key={strategy.strategy_id} className="strategy-card">
                <div className="strategy-header">
                  <h3>{strategy.name}</h3>
                  <div className="strategy-actions">
                    <button
                      onClick={() => handleEdit(strategy.strategy_id)}
                      className="btn btn-sm"
                      title="수정"
                    >
                      ✏️ 수정
                    </button>
                    <button
                      onClick={() => handleBacktest(strategy.strategy_id, strategy.name)}
                      className="btn btn-sm btn-primary"
                      title="백테스트"
                    >
                      📊 백테스트
                    </button>
                    <button
                      onClick={() => handleDelete(strategy.strategy_id, strategy.name)}
                      className="btn btn-sm btn-danger"
                      title="삭제"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                <div className="strategy-info">
                  <p className="description">{strategy.description}</p>
                  <div className="meta">
                    <span className="created-at">
                      생성일: {new Date(strategy.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        .strategy-list-page {
          padding: 20px;
        }

        .page-header-actions {
          margin-bottom: 24px;
          display: flex;
          justify-content: flex-end;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #6b7280;
        }

        .empty-state p {
          margin-bottom: 20px;
          font-size: 16px;
        }

        .strategies-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 20px;
        }

        .strategy-card {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
          transition: box-shadow 0.2s;
        }

        .strategy-card:hover {
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .strategy-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .strategy-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #111827;
        }

        .strategy-actions {
          display: flex;
          gap: 8px;
        }

        .strategy-info .description {
          color: #6b7280;
          font-size: 14px;
          margin-bottom: 12px;
          line-height: 1.5;
        }

        .strategy-info .meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 12px;
          color: #9ca3af;
        }

        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        }

        .btn-sm {
          padding: 4px 8px;
          font-size: 12px;
        }

        .btn-primary {
          background: #3b82f6;
          color: white;
        }

        .btn-primary:hover {
          background: #2563eb;
        }

        .btn-danger {
          background: #ef4444;
          color: white;
        }

        .btn-danger:hover {
          background: #dc2626;
        }

        .btn:not(.btn-primary):not(.btn-danger) {
          background: #f3f4f6;
          color: #374151;
        }

        .btn:not(.btn-primary):not(.btn-danger):hover {
          background: #e5e7eb;
        }
      `}</style>
    </PageLayout>
  );
}
