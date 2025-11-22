"""
계좌 관련 서비스
"""
from typing import List
from datetime import datetime

from broker.ls.client import LSClient
from broker.ls.models.account import LSAccount, LSPosition
from broker.ls.endpoints import LSEndpoints
from utils.logger import setup_logger
from utils.types import Account, Position

logger = setup_logger(__name__)


class LSAccountService:
    """LS증권 계좌 서비스"""
    
    def __init__(self, client: LSClient):
        """
        Args:
            client: LS API 클라이언트
        """
        self.client = client
    
    async def get_account_balance(self, account_id: str) -> LSAccount:
        """
        계좌 잔고 조회 (t0424 - 주식잔고2)
        
        Args:
            account_id: 계좌번호 (예: "555044505-01")
            
        Returns:
            계좌 정보
        """
        try:
            # 계좌번호에서 "-" 제거
            clean_account = account_id.replace("-", "")
            
            # 계좌 비밀번호 (config에서 가져오기)
            from utils.config import config
            password = config.get("ls.account_password", "")
            
            # LS증권 주식잔고 조회 API (t0424)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/accno",
                data={
                    "t0424InBlock": {
                        "accno": clean_account,  # 계좌번호
                        "passwd": password,  # 계좌비밀번호
                        "prcgb": "",  # 단가구분
                        "chegb": "",  # 체결구분
                        "dangb": "",  # 단일가구분
                        "charge": "",  # 수수료구분
                        "cts_expcode": ""  # 연속조회종목코드
                    }
                },
                headers={
                    "tr_id": "t0424",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 응답 파싱
            output = response.get("t0424OutBlock", {})
            
            # 계좌 정보 생성
            return LSAccount(
                account_id=account_id,
                balance=float(output.get("mamt", 0)),  # 예수금
                equity=float(output.get("sunamt", 0)),  # 추정순자산
                stock_value=float(output.get("tappamt", 0)),  # 총평가금액
                profit_loss=float(output.get("tdtsunik", 0)),  # 총평가손익
                profit_loss_rate=0.0,  # 손익률은 별도 계산 필요
                margin_available=float(output.get("sunamt1", 0)),  # 순자산
                deposit=float(output.get("mamt", 0)),  # 예수금
                withdraw_available=float(output.get("mamt", 0)),  # 출금가능금액
                updated_at=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise
    
    async def get_positions(self, account_id: str) -> List[LSPosition]:
        """
        보유 종목 조회 (t0424 - 주식잔고2)
        
        Args:
            account_id: 계좌번호
            
        Returns:
            보유 종목 리스트
        """
        try:
            # 계좌번호에서 "-" 제거
            clean_account = account_id.replace("-", "")
            
            # 계좌 비밀번호
            from utils.config import config
            password = config.get("ls.account_password", "")
            
            # LS증권 주식잔고 조회 API (t0424)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/accno",
                data={
                    "t0424InBlock": {
                        "accno": clean_account,
                        "passwd": password,
                        "prcgb": "",
                        "chegb": "",
                        "dangb": "",
                        "charge": "",
                        "cts_expcode": ""
                    }
                },
                headers={
                    "tr_id": "t0424",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 종목별 잔고 파싱
            positions = []
            for item in response.get("t0424OutBlock1", []):
                # 수익률 계산
                pamt = float(item.get("pamt", 0))  # 매입금액
                dtsunik = float(item.get("dtsunik", 0))  # 평가손익
                profit_rate = (dtsunik / pamt * 100) if pamt > 0 else 0.0
                
                # 평균단가 계산
                janqty = int(item.get("janqty", 0))
                mpms = float(item.get("mpms", 0))
                avg_price = (mpms / janqty) if janqty > 0 else 0.0
                
                position = LSPosition(
                    symbol=item.get("expcode", ""),  # 종목코드
                    name=item.get("hname", ""),  # 종목명
                    quantity=janqty,  # 잔고수량
                    available_quantity=int(item.get("mdposqt", 0)),  # 매도가능수량
                    avg_price=avg_price,  # 평균단가
                    current_price=float(item.get("price", 0)),  # 현재가
                    eval_amount=float(item.get("appamt", 0)),  # 평가금액
                    profit_loss=dtsunik,  # 평가손익
                    profit_loss_rate=profit_rate,  # 수익률
                    buy_amount=pamt,  # 매입금액
                    loan_date=item.get("loandt"),  # 대출일
                    updated_at=datetime.now()
                )
                positions.append(position)
            
            logger.info(f"Found {len(positions)} positions")
            return positions
        
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    async def get_order_available(self, account_id: str) -> float:
        """
        주문 가능 금액 조회 (CSPAQ12200 - 현물계좌예수금/주문가능금액/총평가 조회)
        
        Args:
            account_id: 계좌번호
            
        Returns:
            주문 가능 금액
        """
        try:
            # LS증권 주문가능금액 조회 API (CSPAQ12200)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/accno",
                data={
                    "CSPAQ12200InBlock1": {
                        "RecCnt": 1,
                        "MgmtBrnNo": "1",  # 관리지점번호
                        "BalCreTp": "1"  # 잔고생성구분
                    }
                },
                headers={
                    "tr_id": "CSPAQ12200",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 응답 파싱
            output = response.get("CSPAQ12200OutBlock2", {})
            
            return float(output.get("MnyOrdAbleAmt", 0))  # 현금주문가능금액
        
        except Exception as e:
            logger.error(f"Failed to get order available: {e}")
            raise
    
    def to_account(self, ls_account: LSAccount) -> Account:
        """
        LSAccount를 공통 Account 타입으로 변환
        
        Args:
            ls_account: LS계좌 정보
            
        Returns:
            공통 Account 타입
        """
        return Account(
            account_id=ls_account.account_id,
            balance=ls_account.balance,
            equity=ls_account.equity,
            margin_used=ls_account.margin_used,
            margin_available=ls_account.margin_available
        )
    
    def to_position(self, ls_position: LSPosition) -> Position:
        """
        LSPosition을 공통 Position 타입으로 변환
        
        Args:
            ls_position: LS보유종목
            
        Returns:
            공통 Position 타입
        """
        return Position(
            symbol=ls_position.symbol,
            quantity=ls_position.quantity,
            avg_price=ls_position.avg_price,
            current_price=ls_position.current_price,
            unrealized_pnl=ls_position.profit_loss,
            realized_pnl=0.0  # TODO: 실현손익 추가 필요
        )
