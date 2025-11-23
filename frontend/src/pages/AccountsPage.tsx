import { useState, useEffect } from 'react';
import { PageLayout } from '../components/Layout/PageLayout';
import { httpClient } from '../services/http';

interface TradingAccount {
  id: number;
  name: string;
  broker: string;
  account_type: string;
  account_number_masked: string;
  api_key_masked?: string;
  has_api_secret: boolean;
  has_app_key: boolean;
  has_app_secret: boolean;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
}

const BROKER_NAMES: Record<string, string> = {
  ls: 'LS증권',
  kiwoom: '키움증권',
  kis: '한국투자증권',
  upbit: '업비트',
  binance: '바이낸스',
  mock: '모의투자',
};

const ACCOUNT_TYPE_NAMES: Record<string, string> = {
  real: '실계좌',
  paper: '모의투자',
};

interface AccountsPageProps {
  embedded?: boolean;
}

export default function AccountsPage({ embedded = false }: AccountsPageProps) {
  const [accounts, setAccounts] = useState<TradingAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState<TradingAccount | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    broker: 'ls',
    account_type: 'paper',
    account_number: '',
    api_key: '',
    api_secret: '',
    app_key: '',
    app_secret: '',
    is_default: false,
  });

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await httpClient.get('/api/accounts');
      setAccounts(response.data);
    } catch (error) {
      console.error('계좌 목록 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingAccount(null);
    setFormData({
      name: '',
      broker: 'ls',
      account_type: 'paper',
      account_number: '',
      api_key: '',
      api_secret: '',
      app_key: '',
      app_secret: '',
      is_default: false,
    });
    setShowModal(true);
  };

  const handleEdit = (account: TradingAccount) => {
    setEditingAccount(account);
    setFormData({
      name: account.name,
      broker: account.broker,
      account_type: account.account_type,
      account_number: '',
      api_key: '',
      api_secret: '',
      app_key: '',
      app_secret: '',
      is_default: account.is_default,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingAccount) {
        // 수정
        const updateData: any = { name: formData.name, is_default: formData.is_default };
        if (formData.account_number) updateData.account_number = formData.account_number;
        if (formData.api_key) updateData.api_key = formData.api_key;
        if (formData.api_secret) updateData.api_secret = formData.api_secret;
        if (formData.app_key) updateData.app_key = formData.app_key;
        if (formData.app_secret) updateData.app_secret = formData.app_secret;

        await httpClient.put(`/api/accounts/${editingAccount.id}`, updateData);
      } else {
        // 생성
        await httpClient.post('/api/accounts', formData);
      }
      setShowModal(false);
      loadAccounts();
    } catch (error) {
      console.error('계좌 저장 실패:', error);
      alert('계좌 저장에 실패했습니다.');
    }
  };

  const handleDelete = async (accountId: number) => {
    if (!confirm('정말 이 계좌를 삭제하시겠습니까?')) return;
    try {
      await httpClient.delete(`/api/accounts/${accountId}`);
      loadAccounts();
    } catch (error) {
      console.error('계좌 삭제 실패:', error);
      alert('계좌 삭제에 실패했습니다.');
    }
  };

  const handleToggleActive = async (accountId: number) => {
    try {
      await httpClient.post(`/api/accounts/${accountId}/toggle-active`);
      loadAccounts();
    } catch (error) {
      console.error('계좌 상태 변경 실패:', error);
    }
  };

  const handleSetDefault = async (accountId: number) => {
    try {
      await httpClient.post(`/api/accounts/${accountId}/set-default`);
      loadAccounts();
    } catch (error) {
      console.error('기본 계좌 설정 실패:', error);
    }
  };

  if (loading) {
    return (
      <PageLayout title="계좌 관리">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </PageLayout>
    );
  }

  const content = (
    <>
      <div className="accounts-page">
        {/* 헤더 */}
        <div className="page-header-actions">
          <button onClick={handleCreate} className="btn btn-primary">
            + 새 계좌 추가
          </button>
        </div>

        {/* 계좌 목록 */}
        {accounts.length === 0 ? (
          <div className="empty-state">
            <p>등록된 계좌가 없습니다</p>
            <button onClick={handleCreate} className="btn btn-primary">
              첫 계좌 추가하기
            </button>
          </div>
        ) : (
          <div className="accounts-grid">
            {accounts.map((account) => (
              <div
                key={account.id}
                className={`account-card ${!account.is_active ? 'inactive' : ''}`}
              >
                <div className="account-header">
                  <div>
                    <h3>{account.name}</h3>
                    <div className="account-badges">
                      {account.is_default && <span className="badge badge-primary">기본</span>}
                      {!account.is_active && <span className="badge badge-secondary">비활성</span>}
                    </div>
                  </div>
                  <div className="account-actions">
                    <button onClick={() => handleEdit(account)} className="btn btn-sm">
                      수정
                    </button>
                    {!account.is_default && (
                      <button
                        onClick={() => handleSetDefault(account.id)}
                        className="btn btn-sm btn-primary"
                      >
                        기본으로
                      </button>
                    )}
                    <button
                      onClick={() => handleToggleActive(account.id)}
                      className={`btn btn-sm ${account.is_active ? 'btn-warning' : 'btn-success'}`}
                    >
                      {account.is_active ? '비활성화' : '활성화'}
                    </button>
                    <button
                      onClick={() => handleDelete(account.id)}
                      className="btn btn-sm btn-danger"
                    >
                      삭제
                    </button>
                  </div>
                </div>
                <div className="account-info">
                  <div className="info-row">
                    <span className="label">증권사:</span>
                    <span>{BROKER_NAMES[account.broker] || account.broker}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">타입:</span>
                    <span>{ACCOUNT_TYPE_NAMES[account.account_type] || account.account_type}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">계좌번호:</span>
                    <span>{account.account_number_masked}</span>
                  </div>
                  {account.api_key_masked && (
                    <div className="info-row">
                      <span className="label">API Key:</span>
                      <span>{account.api_key_masked}</span>
                    </div>
                  )}
                  <div className="info-row text-secondary">
                    <span>등록일: {new Date(account.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 모달 */}
        {showModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2>{editingAccount ? '계좌 수정' : '새 계좌 추가'}</h2>
              <form onSubmit={handleSubmit} className="modal-form">
                <div className="form-group">
                  <label>계좌 이름</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="form-input"
                    placeholder="예: LS증권 모의투자"
                    required
                  />
                </div>

                {!editingAccount && (
                  <>
                    <div className="form-group">
                      <label>증권사/거래소</label>
                      <select
                        value={formData.broker}
                        onChange={(e) => setFormData({ ...formData, broker: e.target.value })}
                        className="form-select"
                      >
                        <option value="ls">LS증권</option>
                        <option value="kiwoom">키움증권</option>
                        <option value="kis">한국투자증권</option>
                        <option value="upbit">업비트</option>
                        <option value="binance">바이낸스</option>
                        <option value="mock">모의투자</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>계좌 타입</label>
                      <select
                        value={formData.account_type}
                        onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
                        className="form-select"
                      >
                        <option value="paper">모의투자</option>
                        <option value="real">실계좌</option>
                      </select>
                    </div>
                  </>
                )}

                <div className="form-group">
                  <label>계좌번호 {editingAccount && '(변경 시에만 입력)'}</label>
                  <input
                    type="text"
                    value={formData.account_number}
                    onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                    className="form-input"
                    placeholder="계좌번호"
                    required={!editingAccount}
                  />
                </div>

                <div className="form-group">
                  <label>API Key {editingAccount && '(변경 시에만 입력)'}</label>
                  <input
                    type="text"
                    value={formData.api_key}
                    onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                    className="form-input"
                    placeholder="API Key"
                  />
                </div>

                <div className="form-group">
                  <label>API Secret {editingAccount && '(변경 시에만 입력)'}</label>
                  <input
                    type="password"
                    value={formData.api_secret}
                    onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                    className="form-input"
                    placeholder="API Secret"
                  />
                </div>

                {formData.broker === 'kis' && (
                  <>
                    <div className="form-group">
                      <label>App Key</label>
                      <input
                        type="text"
                        value={formData.app_key}
                        onChange={(e) => setFormData({ ...formData, app_key: e.target.value })}
                        className="form-input"
                        placeholder="App Key"
                      />
                    </div>
                    <div className="form-group">
                      <label>App Secret</label>
                      <input
                        type="password"
                        value={formData.app_secret}
                        onChange={(e) => setFormData({ ...formData, app_secret: e.target.value })}
                        className="form-input"
                        placeholder="App Secret"
                      />
                    </div>
                  </>
                )}

                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.is_default}
                      onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                      style={{ marginRight: '8px' }}
                    />
                    기본 계좌로 설정
                  </label>
                </div>

                <div className="modal-actions">
                  <button type="submit" className="btn btn-primary">
                    {editingAccount ? '수정' : '추가'}
                  </button>
                  <button type="button" onClick={() => setShowModal(false)} className="btn">
                    취소
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );

  if (embedded) {
    return content;
  }

  return (
    <PageLayout title="계좌 관리" description="증권사 및 거래소 계좌를 관리합니다">
      {content}
    </PageLayout>
  );
}
