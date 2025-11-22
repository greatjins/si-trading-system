/**
 * 대시보드 페이지
 */
import { PageLayout } from '../components/Layout/PageLayout';
import { CandlestickChart } from '../modules/chart/components/CandlestickChart';
import { ChartControls } from '../modules/chart/components/ChartControls';
import { OrderPanel } from '../modules/trading/components/OrderPanel';
import { OrderHistory } from '../modules/trading/components/OrderHistory';
import { AccountInfo } from '../modules/account/components/AccountInfo';
import { useChart } from '../modules/chart/hooks/useChart';

export const DashboardPage = () => {
  const { isLoading, error } = useChart();
  
  return (
    <PageLayout title="트레이딩" description="실시간 차트와 주문 관리">
      <div className="dashboard-layout">
        {/* 계좌 정보 */}
        <div className="account-section">
          <AccountInfo />
        </div>
        
        {/* 메인 컨텐츠 */}
        <div className="dashboard-content">
          <div className="main-section">
            <ChartControls />
            
            {error && <div className="error-banner">{error}</div>}
            {isLoading && <div className="loading-banner">데이터 로딩 중...</div>}
            
            <CandlestickChart />
          </div>
          
          <div className="side-section">
            <OrderPanel />
          </div>
        </div>
        
        {/* 주문 내역 */}
        <div className="dashboard-footer">
          <OrderHistory />
        </div>
      </div>
    </PageLayout>
  );
};
