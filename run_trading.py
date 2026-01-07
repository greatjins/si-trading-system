"""
자동매매 시스템 전체 자동화 루프
apscheduler를 사용하여 일일 거래 일정을 자동으로 관리합니다.
"""
import asyncio
import signal
import sys
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.logger import setup_logger
from utils.notifier import get_telegram_notifier, TelegramNotifier
from core.execution.scanner import run_daily_scan
from core.execution.engine import ExecutionEngine
from broker.ls.adapter import LSAdapter
from core.risk.manager import RiskManager
from core.notifications.manager import NotificationManager, NotificationType

logger = setup_logger(__name__)


class SlackNotifier:
    """
    Slack 알림 전송
    
    환경 변수 또는 config에서 다음 설정을 읽습니다:
    - slack.webhook_url: Slack Webhook URL
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Args:
            webhook_url: Slack Webhook URL (None이면 config에서 로드)
        """
        from utils.config import config
        self.webhook_url = webhook_url or config.get("slack.webhook_url", "")
        
        if not self.webhook_url:
            logger.warning("Slack webhook_url not configured. Slack notifications will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("SlackNotifier initialized")
    
    async def send_message(self, message: str) -> bool:
        """
        Slack 메시지 전송
        
        Args:
            message: 전송할 메시지
        
        Returns:
            전송 성공 여부
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping message")
            return False
        
        import aiohttp
        
        payload = {"text": message}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url, 
                    json=payload, 
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.debug("Slack message sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Slack message: {response.status} - {error_text}")
                        return False
        
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
    
    async def send_error(self, error_message: str, error_type: Optional[str] = None, context: Optional[str] = None) -> bool:
        """에러 알림 전송"""
        message = f"⚠️ *에러 발생*\n\n"
        if error_type:
            message += f"*타입:* {error_type}\n"
        message += f"*메시지:* {error_message}\n"
        if context:
            message += f"\n*컨텍스트:* {context}"
        return await self.send_message(message)
    
    async def send_info(self, title: str, message: str) -> bool:
        """정보 알림 전송"""
        formatted_message = f"*{title}*\n\n{message}"
        return await self.send_message(formatted_message)
    
    async def send_success(self, title: str, message: str) -> bool:
        """성공 알림 전송"""
        formatted_message = f"✅ *{title}*\n\n{message}"
        return await self.send_message(formatted_message)


class TradingAutomation:
    """
    자동매매 시스템 전체 자동화 루프
    
    일일 거래 일정을 자동으로 관리하고, 모든 단계의 진행 상황과 
    주문 체결 알림을 Telegram/Slack으로 전송합니다.
    """
    
    def __init__(self):
        """초기화"""
        self.scheduler = AsyncIOScheduler()
        self.telegram_notifier = get_telegram_notifier()
        self.slack_notifier = SlackNotifier()
        self.execution_engine: Optional[ExecutionEngine] = None
        self.broker_adapter: Optional[LSAdapter] = None
        self.risk_manager: Optional[RiskManager] = None
        self.notification_manager = NotificationManager()
        
        # 주문 체결 알림을 위한 콜백 등록
        self._setup_notification_callbacks()
        
        logger.info("TradingAutomation initialized")
    
    def _setup_notification_callbacks(self):
        """알림 콜백 설정"""
        def on_notification(notification):
            """알림 발생 시 Telegram/Slack으로 전송 (동기 래퍼)"""
            # 비동기 함수를 태스크로 실행
            asyncio.create_task(self._send_notification_async(notification))
        
        # NotificationManager에 콜백 등록
        self.notification_manager.add_send_callback(on_notification)
    
    async def _send_notification_async(self, notification):
        """알림을 비동기로 전송"""
        try:
            # 주문 체결 알림
            if notification.type == NotificationType.ORDER_FILLED:
                metadata = notification.metadata or {}
                symbol = metadata.get("symbol", "")
                side = metadata.get("side", "")
                quantity = metadata.get("quantity", 0)
                price = metadata.get("price", 0.0)
                
                message = f"주문 체결: {symbol} {side} {quantity}주 @ {price:,.0f}원"
                
                # Telegram 전송
                await self.telegram_notifier.send_success("주문 체결", message)
                
                # Slack 전송
                await self.slack_notifier.send_success("주문 체결", message)
            
            # 기타 알림
            else:
                if notification.type == NotificationType.ERROR:
                    await self.telegram_notifier.send_error(notification.message, notification.title)
                    await self.slack_notifier.send_error(notification.message, notification.title)
                elif notification.type == NotificationType.STRATEGY_STARTED:
                    await self.telegram_notifier.send_success(notification.title, notification.message)
                    await self.slack_notifier.send_success(notification.title, notification.message)
                else:
                    await self.telegram_notifier.send_info(notification.title, notification.message)
                    await self.slack_notifier.send_info(notification.title, notification.message)
        
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
    
    def start(self):
        """스케줄러 시작 및 작업 등록"""
        # 08:10: 전종목 스캔 실행
        self.scheduler.add_job(
            self.job_daily_scan,
            CronTrigger(hour=8, minute=10),
            id="daily_scan",
            name="전종목 스캔",
            timezone="Asia/Seoul"
        )
        
        # 08:30: ExecutionEngine 가동 (NXT 시장 대응)
        self.scheduler.add_job(
            self.job_start_engine,
            CronTrigger(hour=8, minute=30),
            id="start_engine",
            name="실시간 엔진 가동 (NXT 시장)",
            timezone="Asia/Seoul"
        )
        
        # 09:00: KRX 정규장 매매 활성화
        self.scheduler.add_job(
            self.job_market_open,
            CronTrigger(hour=9, minute=0),
            id="market_open",
            name="KRX 정규장 시작",
            timezone="Asia/Seoul"
        )
        
        # 15:30: 장 마감 후 당일 수익률 정산 및 리포트 생성
        self.scheduler.add_job(
            self.job_market_close,
            CronTrigger(hour=15, minute=30),
            id="market_close",
            name="장 마감 정산 및 리포트",
            timezone="Asia/Seoul"
        )
        
        self.scheduler.start()
        logger.info("TradingAutomation scheduler started")
        
        # 시작 알림
        asyncio.create_task(self._send_startup_notification())
    
    async def _send_startup_notification(self):
        """시작 알림 전송"""
        try:
            message = "자동매매 시스템이 시작되었습니다.\n\n등록된 스케줄:\n- 08:10: 전종목 스캔\n- 08:30: 실시간 엔진 가동\n- 09:00: KRX 정규장 시작\n- 15:30: 장 마감 정산"
            await self.telegram_notifier.send_info("시스템 시작", message)
            await self.slack_notifier.send_info("시스템 시작", message)
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    async def job_daily_scan(self):
        """08:10 작업: 전종목 스캔 실행"""
        try:
            logger.info("=" * 60)
            logger.info("Starting job: 전종목 스캔 (08:10)")
            logger.info("=" * 60)
            
            # scanner.run_daily_scan() 실행
            filtered_symbols = await run_daily_scan()
            
            logger.info(f"Daily scan completed: {len(filtered_symbols)} symbols filtered")
            
            # 알림 전송
            symbol_list = ", ".join(filtered_symbols[:10])
            if len(filtered_symbols) > 10:
                symbol_list += f" 외 {len(filtered_symbols) - 10}개"
            
            message = (
                f"전종목 스캔이 완료되었습니다.\n\n"
                f"필터링된 종목 수: {len(filtered_symbols)}개\n"
                f"종목 목록: {symbol_list}"
            )
            
            await self.telegram_notifier.send_success("전종목 스캔 완료", message)
            await self.slack_notifier.send_success("전종목 스캔 완료", message)
            
        except Exception as e:
            error_msg = f"전종목 스캔 실패: {e}"
            logger.error(error_msg, exc_info=True)
            await self.telegram_notifier.send_error(error_msg, "ScanError", "전종목 스캔")
            await self.slack_notifier.send_error(error_msg, "ScanError", "전종목 스캔")
            raise
    
    async def job_start_engine(self):
        """08:30 작업: ExecutionEngine 가동 (NXT 시장 대응)"""
        try:
            logger.info("=" * 60)
            logger.info("Starting job: 실시간 엔진 가동 (08:30)")
            logger.info("=" * 60)
            
            # Broker Adapter 초기화
            if self.broker_adapter is None:
                self.broker_adapter = LSAdapter()
                await self.broker_adapter.__aenter__()
                logger.info("Broker adapter initialized")
            
            # Risk Manager 초기화
            if self.risk_manager is None:
                self.risk_manager = RiskManager(
                    max_position_size=0.1,
                    max_daily_loss=0.05,
                    max_drawdown=0.15
                )
                logger.info("Risk manager initialized")
            
            # ExecutionEngine 생성 (DB에서 전략 설정 로드)
            if self.execution_engine is None:
                self.execution_engine = await ExecutionEngine.create_from_db_config(
                    broker=self.broker_adapter,
                    risk_manager=self.risk_manager,
                    notification_manager=self.notification_manager
                )
                logger.info("Execution engine created")
            
            # active_universe에서 종목 리스트 읽어와 엔진 시작
            await self.execution_engine.start_with_active_universe()
            
            logger.info("Execution engine started (NXT 시장 대기 중)")
            
            # 알림 전송
            message = (
                "실시간 엔진이 가동되었습니다.\n\n"
                "현재 NXT 시장(넥스트레이드) 대기 중입니다.\n"
                "09:00에 KRX 정규장이 시작되면 매매가 활성화됩니다."
            )
            
            await self.telegram_notifier.send_success("실시간 엔진 가동", message)
            await self.slack_notifier.send_success("실시간 엔진 가동", message)
            
        except Exception as e:
            error_msg = f"실시간 엔진 가동 실패: {e}"
            logger.error(error_msg, exc_info=True)
            await self.telegram_notifier.send_error(error_msg, "EngineStartError")
            await self.slack_notifier.send_error(error_msg, "EngineStartError")
            raise
    
    async def job_market_open(self):
        """09:00 작업: KRX 정규장 매매 활성화"""
        try:
            logger.info("=" * 60)
            logger.info("Starting job: KRX 정규장 시작 (09:00)")
            logger.info("=" * 60)
            
            # ExecutionEngine이 이미 가동 중이므로 별도 작업 없음
            # determine_market()이 자동으로 "KRX"를 반환하므로 매매가 활성화됨
            
            message = (
                "KRX 정규장이 시작되었습니다.\n\n"
                "매매가 활성화되었습니다.\n"
                "실시간 시세 감시 및 주문 실행이 진행됩니다."
            )
            
            await self.telegram_notifier.send_info("KRX 정규장 시작", message)
            await self.slack_notifier.send_info("KRX 정규장 시작", message)
            
        except Exception as e:
            error_msg = f"KRX 정규장 시작 알림 실패: {e}"
            logger.error(error_msg, exc_info=True)
            await self.telegram_notifier.send_error(error_msg, "JobError", "KRX 정규장 시작")
            await self.slack_notifier.send_error(error_msg, "JobError", "KRX 정규장 시작")
    
    async def job_market_close(self):
        """15:30 작업: 장 마감 후 당일 수익률 정산 및 리포트 생성"""
        try:
            logger.info("=" * 60)
            logger.info("Starting job: 장 마감 정산 및 리포트 (15:30)")
            logger.info("=" * 60)
            
            # 1. 계좌 정보 조회
            if self.broker_adapter is None:
                logger.warning("Broker adapter not initialized, skipping settlement")
                return
            
            account = await self.broker_adapter.get_account()
            positions = await self.broker_adapter.get_positions()
            
            # 2. 일일 수익률 계산
            daily_report = await self._calculate_daily_report(account, positions)
            
            # 3. 리포트 생성
            report_text = self._generate_daily_report(daily_report)
            
            # 4. 리포트 파일 저장
            report_file = self._save_daily_report(report_text, daily_report)
            
            logger.info(f"Daily report generated: {report_file}")
            
            # 5. 알림 전송 (리포트 요약)
            message = (
                f"KRX 정규장이 마감되었습니다.\n\n"
                f"📊 일일 수익률 정산 결과:\n"
                f"• 현재 자산: {account.equity:,.0f}원\n"
                f"• 일일 수익률: {daily_report['daily_return']:.2%}\n"
                f"• 일일 손익: {daily_report['daily_pnl']:+,.0f}원\n"
                f"• 총 거래 횟수: {daily_report['total_trades']}회\n"
                f"• 보유 종목 수: {len(positions)}개\n\n"
                f"리포트 파일: {report_file}"
            )
            
            await self.telegram_notifier.send_info("장 마감 정산 완료", message)
            await self.slack_notifier.send_info("장 마감 정산 완료", message)
            
        except Exception as e:
            error_msg = f"장 마감 정산 실패: {e}"
            logger.error(error_msg, exc_info=True)
            await self.telegram_notifier.send_error(error_msg, "JobError", "장 마감 정산")
            await self.slack_notifier.send_error(error_msg, "JobError", "장 마감 정산")
    
    async def _calculate_daily_report(self, account, positions) -> dict:
        """
        일일 수익률 정산
        
        Args:
            account: 계좌 정보
            positions: 포지션 리스트
        
        Returns:
            일일 리포트 데이터
        """
        from data.repository import get_db_session
        from data.models import StrategyPerformanceModel
        from datetime import date
        
        today = date.today()
        
        # 전일 자산 조회 (DB에서)
        session = get_db_session()
        try:
            # 전략 성과 모델에서 전일 자산 조회
            yesterday = today - timedelta(days=1)
            prev_performance = session.query(StrategyPerformanceModel).filter(
                StrategyPerformanceModel.is_active == True
            ).first()
            
            prev_equity = prev_performance.current_equity if prev_performance else account.equity
            initial_capital = prev_performance.initial_capital if prev_performance else account.equity
            
            # 일일 수익률 계산
            daily_pnl = account.equity - prev_equity
            daily_return = daily_pnl / prev_equity if prev_equity > 0 else 0.0
            
            # 총 거래 횟수 (간단한 구현: 포지션 수 기반)
            total_trades = len(positions)
            
            # 미실현 손익 계산
            unrealized_pnl = sum(
                (pos.current_price - pos.avg_price) * pos.quantity 
                for pos in positions 
                if pos.quantity > 0
            )
            
            return {
                "date": today,
                "current_equity": account.equity,
                "prev_equity": prev_equity,
                "initial_capital": initial_capital,
                "daily_pnl": daily_pnl,
                "daily_return": daily_return,
                "total_return": (account.equity - initial_capital) / initial_capital if initial_capital > 0 else 0.0,
                "total_trades": total_trades,
                "unrealized_pnl": unrealized_pnl,
                "positions": positions
            }
        
        finally:
            session.close()
    
    def _generate_daily_report(self, report_data: dict) -> str:
        """
        일일 리포트 텍스트 생성
        
        Args:
            report_data: 리포트 데이터
        
        Returns:
            리포트 텍스트
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("일일 수익률 정산 리포트")
        report_lines.append("=" * 60)
        report_lines.append(f"날짜: {report_data['date']}")
        report_lines.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("[자산 현황]")
        report_lines.append(f"초기 자본: {report_data['initial_capital']:,.0f}원")
        report_lines.append(f"전일 자산: {report_data['prev_equity']:,.0f}원")
        report_lines.append(f"현재 자산: {report_data['current_equity']:,.0f}원")
        report_lines.append("")
        
        report_lines.append("[일일 성과]")
        report_lines.append(f"일일 손익: {report_data['daily_pnl']:+,.0f}원")
        report_lines.append(f"일일 수익률: {report_data['daily_return']:.2%}")
        report_lines.append(f"총 수익률: {report_data['total_return']:.2%}")
        report_lines.append("")
        
        report_lines.append("[거래 현황]")
        report_lines.append(f"총 거래 횟수: {report_data['total_trades']}회")
        report_lines.append(f"보유 종목 수: {len(report_data['positions'])}개")
        report_lines.append(f"미실현 손익: {report_data['unrealized_pnl']:+,.0f}원")
        report_lines.append("")
        
        if report_data['positions']:
            report_lines.append("[보유 종목]")
            for pos in report_data['positions']:
                if pos.quantity > 0:
                    pnl = (pos.current_price - pos.avg_price) * pos.quantity
                    pnl_rate = (pos.current_price / pos.avg_price - 1) if pos.avg_price > 0 else 0.0
                    report_lines.append(
                        f"{pos.symbol}: {pos.quantity}주 @ {pos.avg_price:,.0f}원 "
                        f"(현재가: {pos.current_price:,.0f}원, 손익: {pnl:+,.0f}원, {pnl_rate:.2%})"
                    )
            report_lines.append("")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def _save_daily_report(self, report_text: str, report_data: dict) -> str:
        """
        일일 리포트 파일 저장
        
        Args:
            report_text: 리포트 텍스트
            report_data: 리포트 데이터
        
        Returns:
            저장된 파일 경로
        """
        from utils.config import config
        
        # 리포트 디렉토리 생성
        report_dir = Path(config.get("reports.directory", "reports"))
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명: daily_report_YYYYMMDD.txt
        date_str = report_data['date'].strftime("%Y%m%d")
        filename = f"daily_report_{date_str}.txt"
        filepath = report_dir / filename
        
        # 파일 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"Daily report saved: {filepath}")
        return str(filepath)
    
    async def stop(self):
        """스케줄러 중지 및 리소스 정리"""
        logger.info("Stopping TradingAutomation...")
        
        # ExecutionEngine 중지
        if self.execution_engine:
            try:
                await self.execution_engine.stop()
                self.execution_engine = None
                logger.info("Execution engine stopped")
            except Exception as e:
                logger.error(f"Error stopping execution engine: {e}")
        
        # Broker Adapter 정리
        if self.broker_adapter:
            try:
                await self.broker_adapter.__aexit__(None, None, None)
                self.broker_adapter = None
                logger.info("Broker adapter closed")
            except Exception as e:
                logger.error(f"Error closing broker adapter: {e}")
        
        # 스케줄러 중지
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
        
        # 종료 알림
        try:
            message = "자동매매 시스템이 종료되었습니다."
            await self.telegram_notifier.send_info("시스템 종료", message)
            await self.slack_notifier.send_info("시스템 종료", message)
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")


# 전역 인스턴스
_automation: Optional[TradingAutomation] = None


def signal_handler(signum, frame):
    """시그널 핸들러 (Ctrl+C 등)"""
    logger.info("Received shutdown signal, stopping automation...")
    if _automation:
        asyncio.create_task(_automation.stop())
    sys.exit(0)


async def main():
    """메인 함수"""
    global _automation
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # TradingAutomation 초기화 및 시작
    _automation = TradingAutomation()
    _automation.start()
    
    logger.info("=" * 60)
    logger.info("자동매매 시스템이 시작되었습니다.")
    logger.info("=" * 60)
    logger.info("등록된 스케줄:")
    logger.info("  - 08:10: 전종목 스캔")
    logger.info("  - 08:30: 실시간 엔진 가동 (NXT 시장)")
    logger.info("  - 09:00: KRX 정규장 시작")
    logger.info("  - 15:30: 장 마감 정산 및 리포트")
    logger.info("=" * 60)
    
    # 무한 대기 (스케줄러가 백그라운드에서 실행)
    try:
        while True:
            await asyncio.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        if _automation:
            await _automation.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

