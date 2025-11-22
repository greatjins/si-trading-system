"""
LS증권 계좌 정보 조회
"""
from typing import List

from broker.ls.client import LSClient
from utils.types import Account, Position, Order, OrderStatus, OrderSide, OrderType
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class LSAccountService:
    """LS증권 계좌 서비스"""
    
    def __init__(self, client: LSClient):
        self.client = client
    
    async def get_account_balance(self) -> Account:
        """
        계좌 잔고 조회
        
        Returns:
            계좌 정보
        """
        logger.info(f"Fetching account balance for {self.client.account_id}")
        
        # TODO: 실제 LS증권 계좌잔고 API 호출
        # 예시 엔드포인트: /uapi/domestic-stock/v1/trading/inquire-psbl-order
        
        try:
            # response = await self.client.get("/uapi/domestic-stock/v1/trading/inquire-psbl-order", params={
            #     "CANO": self.client.account_id,
            #     "ACNT_PRDT_CD": "01"
            # })
            # data = response.get("output", {})
            
            # Mock 계좌 정보 (개발용)
            logger.warning("Using MOCK account data - implement actual API call")
            return Account(
                account_id=self.client.account_id,
                balance=10_000_000.0,
                equity=10_000_000.0,
                margin_used=0.0,
                margin_available=10_000_000.0
            )
        
        except Exception as e:
            logger.error(f"Failed to fetch account balance: {e}")
            raise
    
    async def get_positions(self) -> List[Position]:
        """
        보유 종목 조회
        
        Returns:
            포지션 리스트
        """
        logger.info(f"Fetching positions for {self.client.account_id}")
        
        # TODO: 실제 LS증권 보유종목 API 호출
        # 예시 엔드포인트: /uapi/domestic-stock/v1/trading/inquire-balance
        
        try:
            # response = await self.client.get("/uapi/domestic-stock/v1/trading/inquire-balance", params={
            #     "CANO": self.client.account_id,
            #     "ACNT_PRDT_CD": "01",
            #     "AFHR_FLPR_YN": "N",
            #     "OFL_YN": "N",
            #     "INQR_DVSN": "01",
            #     "UNPR_DVSN": "01",
            #     "FUND_STTL_ICLD_YN": "N",
            #     "FNCG_AMT_AUTO_RDPT_YN": "N",
            #     "PRCS_DVSN": "00",
            #     "CTX_AREA_FK100": "",
            #     "CTX_AREA_NK100": ""
            # })
            # 
            # positions_data = response.get("output1", [])
            # positions = self._parse_positions(positions_data)
            
            # Mock 포지션 (개발용)
            logger.warning("Using MOCK positions - implement actual API call")
            return []
        
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            raise
    
    async def get_open_orders(self) -> List[Order]:
        """
        미체결 주문 조회
        
        Returns:
            미체결 주문 리스트
        """
        logger.info(f"Fetching open orders for {self.client.account_id}")
        
        # TODO: 실제 LS증권 미체결주문 API 호출
        # 예시 엔드포인트: /uapi/domestic-stock/v1/trading/inquire-daily-ccld
        
        try:
            # Mock 미체결 주문 (개발용)
            logger.warning("Using MOCK open orders - implement actual API call")
            return []
        
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            raise
    
    def _parse_positions(self, data: List[dict]) -> List[Position]:
        """API 응답을 Position 타입으로 변환"""
        positions: List[Position] = []
        
        for item in data:
            try:
                position = Position(
                    symbol=item.get("pdno", ""),
                    quantity=int(item.get("hldg_qty", "0")),
                    avg_price=float(item.get("pchs_avg_pric", "0")),
                    current_price=float(item.get("prpr", "0")),
                    unrealized_pnl=float(item.get("evlu_pfls_amt", "0")),
                    realized_pnl=0.0
                )
                positions.append(position)
            except Exception as e:
                logger.warning(f"Failed to parse position data: {e}")
                continue
        
        return positions
