"""
일봉 스캐너 - ICT 지표 기반 종목 필터링
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd

from data.repository import DataRepository, get_db_session
from utils.indicators import calculate_fvg, calculate_order_block
from utils.logger import setup_logger
from data.models import ActiveUniverseModel

logger = setup_logger(__name__)


class Scanner:
    """
    일봉 스캐너
    
    모든 상장 종목(또는 거래대금 상위 200종목)의 일봉 데이터를 분석하여
    ICT 지표(FVG, Order Block)를 활용해 유효한 종목을 필터링합니다.
    """
    
    def __init__(self, repository: Optional[DataRepository] = None):
        """
        Args:
            repository: DataRepository 인스턴스 (None이면 자동 생성)
        """
        self.repository = repository or DataRepository()
        logger.info("Scanner initialized")
    
    async def get_stock_list(
        self, 
        use_top_volume: bool = True, 
        top_count: int = 200
    ) -> List[str]:
        """
        스캔할 종목 리스트 가져오기
        
        Args:
            use_top_volume: True면 거래대금 상위 종목, False면 전체 상장 종목
            top_count: 거래대금 상위 종목 개수 (기본: 200)
        
        Returns:
            종목 코드 리스트
        """
        if use_top_volume:
            # 거래대금 상위 종목 조회
            try:
                from broker.ls.adapter import LSAdapter
                async with LSAdapter() as adapter:
                    top_stocks = await adapter.market_service.get_top_volume_stocks(
                        market="0",  # 0:전체
                        count=top_count
                    )
                    symbols = [stock["symbol"] for stock in top_stocks]
                    logger.info(f"Fetched {len(symbols)} top volume stocks")
                    return symbols
            except Exception as e:
                logger.error(f"Failed to get top volume stocks: {e}")
                # 폴백: DB에서 거래대금 상위 종목 조회
                return self._get_top_volume_from_db(top_count)
        else:
            # 전체 상장 종목 조회
            try:
                from broker.ls.adapter import LSAdapter
                async with LSAdapter() as adapter:
                    all_stocks = await adapter.market_service.get_all_symbols(market="0")
                    symbols = [stock["symbol"] for stock in all_stocks]
                    logger.info(f"Fetched {len(symbols)} all listed stocks")
                    return symbols
            except Exception as e:
                logger.error(f"Failed to get all symbols: {e}")
                # 폴백: DB에서 활성 종목 조회
                return self._get_all_symbols_from_db()
    
    def _get_top_volume_from_db(self, count: int) -> List[str]:
        """DB에서 거래대금 상위 종목 조회"""
        session = get_db_session()
        try:
            from data.models import StockMasterModel
            stocks = session.query(StockMasterModel).filter_by(
                is_active=True
            ).order_by(
                StockMasterModel.volume_amount.desc()
            ).limit(count).all()
            return [s.symbol for s in stocks]
        finally:
            session.close()
    
    def _get_all_symbols_from_db(self) -> List[str]:
        """DB에서 전체 활성 종목 조회"""
        session = get_db_session()
        try:
            from data.models import StockMasterModel
            stocks = session.query(StockMasterModel).filter_by(
                is_active=True
            ).all()
            return [s.symbol for s in stocks]
        finally:
            session.close()
    
    def filter_by_ict_indicators(
        self, 
        daily_bars: pd.DataFrame,
        current_price: Optional[float] = None
    ) -> bool:
        """
        ICT 지표를 활용해 종목 필터링
        
        조건:
        1. 일봉상 유효한 FVG가 있거나
        2. Order Block 근처에 현재가가 있는 경우
        
        Args:
            daily_bars: 일봉 DataFrame (columns: open, high, low, close, volume)
            current_price: 현재가 (None이면 최근 종가 사용)
        
        Returns:
            필터링 통과 여부 (True: 유효한 종목)
        """
        if daily_bars.empty or len(daily_bars) < 10:
            return False
        
        # 현재가 설정
        if current_price is None:
            current_price = float(daily_bars['close'].iloc[-1])
        
        # FVG 계산
        daily_bars_with_fvg = calculate_fvg(daily_bars.copy())
        
        # Order Block 계산
        daily_bars_with_ob = calculate_order_block(
            daily_bars.copy(),
            lookback=20,
            volume_multiplier=1.5
        )
        
        # 1. 유효한 FVG 확인 (채워지지 않은 FVG)
        valid_fvg = False
        if 'fvg_type' in daily_bars_with_fvg.columns:
            # 최근 20개 봉에서 유효한 FVG 찾기
            recent_bars = daily_bars_with_fvg.tail(20)
            for idx, row in recent_bars.iterrows():
                fvg_type = row.get('fvg_type')
                fvg_filled = row.get('fvg_filled')
                fvg_top = row.get('fvg_top')
                fvg_bottom = row.get('fvg_bottom')
                
                # 유효한 FVG: 채워지지 않았고, 현재가가 FVG 구간 근처에 있음
                if (fvg_type is not None and 
                    (fvg_filled is False or pd.isna(fvg_filled)) and
                    fvg_top is not None and fvg_bottom is not None):
                    
                    # 현재가가 FVG 구간 근처 (5% 이내)에 있는지 확인
                    fvg_mid = (fvg_top + fvg_bottom) / 2
                    distance_pct = abs(current_price - fvg_mid) / fvg_mid
                    
                    if distance_pct <= 0.05:  # 5% 이내
                        valid_fvg = True
                        logger.debug(f"Valid FVG found: {fvg_type}, top={fvg_top:.0f}, bottom={fvg_bottom:.0f}, current={current_price:.0f}")
                        break
        
        # 2. Order Block 근처 확인
        near_order_block = False
        if 'order_block_type' in daily_bars_with_ob.columns:
            # 최근 20개 봉에서 Order Block 찾기
            recent_bars = daily_bars_with_ob.tail(20)
            for idx, row in recent_bars.iterrows():
                ob_type = row.get('order_block_type')
                ob_top = row.get('order_block_top')
                ob_bottom = row.get('order_block_bottom')
                
                # Order Block이 있고, 현재가가 구간 근처에 있음
                if (ob_type is not None and 
                    ob_top is not None and ob_bottom is not None):
                    
                    # 현재가가 Order Block 구간 근처 (5% 이내)에 있는지 확인
                    ob_mid = (ob_top + ob_bottom) / 2
                    distance_pct = abs(current_price - ob_mid) / ob_mid
                    
                    if distance_pct <= 0.05:  # 5% 이내
                        near_order_block = True
                        logger.debug(f"Near Order Block: {ob_type}, top={ob_top:.0f}, bottom={ob_bottom:.0f}, current={current_price:.0f}")
                        break
        
        # 필터링 통과: 유효한 FVG가 있거나 Order Block 근처에 있음
        return valid_fvg or near_order_block
    
    async def run_daily_scan(
        self,
        use_top_volume: bool = True,
        top_count: int = 200,
        lookback_days: int = 100
    ) -> List[str]:
        """
        일일 스캔 실행
        
        Args:
            use_top_volume: True면 거래대금 상위 종목, False면 전체 상장 종목
            top_count: 거래대금 상위 종목 개수
            lookback_days: 일봉 데이터 조회 기간 (일)
        
        Returns:
            필터링된 종목 코드 리스트
        """
        logger.info(f"Starting daily scan (use_top_volume={use_top_volume}, top_count={top_count})")
        
        # 1. 종목 리스트 가져오기
        symbols = await self.get_stock_list(use_top_volume, top_count)
        logger.info(f"Scanning {len(symbols)} stocks...")
        
        # 2. 각 종목의 일봉 데이터 분석
        filtered_symbols = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        for idx, symbol in enumerate(symbols, 1):
            try:
                # 일봉 데이터 조회
                daily_bars = self.repository.get_ohlc(
                    symbol=symbol,
                    interval="1d",
                    start_date=start_date,
                    end_date=end_date
                )
                
                if daily_bars.empty or len(daily_bars) < 10:
                    logger.debug(f"[{idx}/{len(symbols)}] {symbol}: Insufficient data")
                    continue
                
                # 현재가 조회
                try:
                    from broker.ls.adapter import LSAdapter
                    async with LSAdapter() as adapter:
                        current_price = await adapter.get_current_price(symbol)
                except Exception as e:
                    logger.debug(f"Failed to get current price for {symbol}: {e}, using last close price")
                    current_price = float(daily_bars['close'].iloc[-1])
                
                # ICT 지표 필터링
                if self.filter_by_ict_indicators(daily_bars, current_price):
                    filtered_symbols.append(symbol)
                    logger.info(f"[{idx}/{len(symbols)}] {symbol}: PASSED (FVG/Order Block detected)")
                else:
                    logger.debug(f"[{idx}/{len(symbols)}] {symbol}: Filtered out")
                
                # Rate limit 고려 (API 호출 제한)
                if idx % 10 == 0:
                    import asyncio
                    await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"[{idx}/{len(symbols)}] {symbol}: Error - {e}")
                continue
        
        logger.info(f"Daily scan completed: {len(filtered_symbols)}/{len(symbols)} stocks passed")
        return filtered_symbols
    
    def save_to_active_universe(self, symbols: List[str]) -> None:
        """
        필터링된 종목 리스트를 DB의 'active_universe' 테이블에 저장
        
        Args:
            symbols: 종목 코드 리스트
        """
        session = get_db_session()
        try:
            # 기존 데이터 삭제 (오늘 날짜 기준)
            today = datetime.now().date()
            # scan_date는 DateTime이므로 날짜 비교를 위해 datetime으로 변환
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            session.query(ActiveUniverseModel).filter(
                ActiveUniverseModel.scan_date >= today_start,
                ActiveUniverseModel.scan_date <= today_end
            ).delete()
            
            # 새 데이터 저장 (날짜를 datetime으로 저장)
            today_datetime = datetime.combine(today, datetime.min.time())
            for symbol in symbols:
                universe = ActiveUniverseModel(
                    symbol=symbol,
                    scan_date=today_datetime,
                    created_at=datetime.now()
                )
                session.add(universe)
            
            session.commit()
            logger.info(f"Saved {len(symbols)} symbols to active_universe table")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save to active_universe: {e}")
            raise
        finally:
            session.close()


async def run_daily_scan() -> List[str]:
    """
    일일 스캔 실행 (외부 호출용)
    
    Returns:
        필터링된 종목 코드 리스트
    """
    scanner = Scanner()
    filtered_symbols = await scanner.run_daily_scan()
    scanner.save_to_active_universe(filtered_symbols)
    return filtered_symbols

