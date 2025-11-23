import { useState } from 'react';
import { PageLayout } from '../components/Layout/PageLayout';
import AccountsPage from './AccountsPage';

type TabType = 'accounts' | 'profile' | 'password';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('accounts');

  return (
    <PageLayout title="설정" description="계좌 및 프로필 관리">
      <div className="settings-page">
        {/* 탭 메뉴 */}
        <div className="settings-tabs">
          <button
            className={`tab ${activeTab === 'accounts' ? 'active' : ''}`}
            onClick={() => setActiveTab('accounts')}
          >
            💳 계좌 관리
          </button>
          <button
            className={`tab ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            👤 프로필
          </button>
          <button
            className={`tab ${activeTab === 'password' ? 'active' : ''}`}
            onClick={() => setActiveTab('password')}
          >
            🔐 비밀번호 변경
          </button>
        </div>

        {/* 탭 컨텐츠 */}
        <div className="settings-content">
          {activeTab === 'accounts' && <AccountsPage embedded />}
          {activeTab === 'profile' && <ProfileTab />}
          {activeTab === 'password' && <PasswordTab />}
        </div>
      </div>
    </PageLayout>
  );
}

function ProfileTab() {
  return (
    <div className="settings-tab-content">
      <h3>프로필 정보</h3>
      <div className="form-group">
        <label>사용자명</label>
        <input type="text" className="form-input" value="testuser" disabled />
      </div>
      <div className="form-group">
        <label>이메일</label>
        <input type="email" className="form-input" value="test@example.com" />
      </div>
      <button className="btn btn-primary">저장</button>
    </div>
  );
}

function PasswordTab() {
  return (
    <div className="settings-tab-content">
      <h3>비밀번호 변경</h3>
      <div className="form-group">
        <label>현재 비밀번호</label>
        <input type="password" className="form-input" />
      </div>
      <div className="form-group">
        <label>새 비밀번호</label>
        <input type="password" className="form-input" />
      </div>
      <div className="form-group">
        <label>새 비밀번호 확인</label>
        <input type="password" className="form-input" />
      </div>
      <button className="btn btn-primary">변경</button>
    </div>
  );
}
