import { useState, useEffect } from 'react';
import { httpClient } from '../services/http';
import { Link } from 'react-router-dom';
import { useAccountStore } from '../app/store/accountStore';

interface Account {
  id: number;
  name: string;
  broker: string;
  account_type: string;
  is_default: boolean;
}

export function AccountSelector() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const { selectedAccountId, setSelectedAccountId } = useAccountStore();

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await httpClient.get('/api/accounts?active_only=true');
      const accountList = response.data;
      setAccounts(accountList);
      
      // 기본 계좌 선택
      const defaultAccount = accountList.find((acc: Account) => acc.is_default);
      if (defaultAccount) {
        setSelectedAccountId(defaultAccount.id);
      } else if (accountList.length > 0) {
        setSelectedAccountId(accountList[0].id);
      }
    } catch (error) {
      console.error('계좌 목록 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="account-selector">로딩 중...</div>;
  }

  if (accounts.length === 0) {
    return (
      <div className="account-selector empty">
        <span>등록된 계좌가 없습니다</span>
        <Link to="/settings" className="btn btn-sm btn-primary">
          계좌 추가
        </Link>
      </div>
    );
  }

  return (
    <div className="account-selector">
      <label>거래 계좌</label>
      <select
        value={selectedAccountId || ''}
        onChange={(e) => setSelectedAccountId(Number(e.target.value))}
        className="form-select"
      >
        {accounts.map((account) => (
          <option key={account.id} value={account.id}>
            {account.name} ({account.account_type === 'paper' ? '모의' : '실계좌'})
          </option>
        ))}
      </select>
      <Link to="/settings" className="settings-link">
        ⚙️ 계좌 관리
      </Link>
    </div>
  );
}
