"""
LS증권 주문 서비스
"""
from typing import Optional, List
from datetime import datetime

from broker.ls.client import LSClient
from broker.ls.models.order import LSOrder, LSExecution
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


class LSOrderService:
    """LS증권 주문 서비스"""
    
    def __init__(self, client: LSClient):
        self.client = client
    
    async def place_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "limit",
        price: Optional[float] = None
    ) -> str:
        """
        주문 실행 (CSPAT00601 - 현물주문)
        
        Args:
            account_id: 계좌번호
            symbol: 종목코드
            side: 매수/매도 (buy/sell)
            quantity: 수량
            order_type: 주문 유형 (limit/market)
            price: 가격 (지정가 주문 시)
            
        Returns:
            주문번호
        """
        logger.info(f"Placing order: {side} {quantity} {symbol} @ {price}")
        
        try:
            # 계좌번호에서 "-" 제거
            clean_account = account_id.replace("-", "")
            
            # 계좌 비밀번호
            password = config.get("ls.account_password", "")
            
            # 매수/매도 구분 (1:매도, 2:매수)
            buy_sell_gb = "2" if side.lower() == "buy" else "1"
            
            # 주문 유형 (00:지정가, 03:시장가)
            order_type_code = "03" if order_type.lower() == "market" else "00"
            
            # 주문 가격 (시장가는 0)
            order_price = 0 if order_type.lower() == "market" else int(price)
            
            # LS증권 현물주문 API (CSPAT00601)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/order",
                data={
                    "CSPAT00601InBlock1": {
                        "AcntNo": clean_account,
                        "InptPwd": password,
                        "IsuNo": symbol,
                        "OrdQty": quantity,
                        "OrdPrc": order_price,
                        "BnsTpCode": buy_sell_gb,
                        "OrdprcPtnCode": order_type_code,
                        "MgntrnCode": "000",  # 신용거래코드
                        "LoanDt": "",  # 대출일
                        "OrdCndiTpCode": "0"  # 주문조건구분
                    }
                },
                headers={
                    "tr_id": "CSPAT00601",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 주문번호 추출
            output = response.get("CSPAT00601OutBlock1", {})
            order_id = output.get("OrdNo", "")
            
            logger.info(f"Order placed: {order_id}")
            return order_id
        
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    async def modify_order(
        self,
        account_id: str,
        order_id: str,
        symbol: str,
        quantity: int,
        price: float,
        order_type: str = "limit"
    ) -> str:
        """
        주문 정정 (CSPAT00701 - 현물정정주문)
        
        Args:
            account_id: 계좌번호
            order_id: 원주문번호
            symbol: 종목코드
            quantity: 정정수량
            price: 정정가격
            order_type: 주문 유형 (limit/market)
            
        Returns:
            정정주문번호
        """
        logger.info(f"Modifying order: {order_id} -> {quantity}@{price}")
        
        try:
            clean_account = account_id.replace("-", "")
            password = config.get("ls.account_password", "")
            
            # 주문 유형 (00:지정가, 03:시장가)
            order_type_code = "03" if order_type.lower() == "market" else "00"
            
            # 주문 가격 (시장가는 0)
            order_price = 0 if order_type.lower() == "market" else int(price)
            
            # LS증권 현물정정주문 API (CSPAT00701)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/order",
                data={
                    "CSPAT00701InBlock1": {
                        "OrgOrdNo": order_id,
                        "IsuNo": symbol,
                        "OrdQty": quantity,
                        "OrdprcPtnCode": order_type_code,
                        "OrdCndiTpCode": "0",  # 주문조건구분 (0:없음)
                        "OrdPrc": order_price
                    }
                },
                headers={
                    "tr_id": "CSPAT00701",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 정정주문번호 추출
            output = response.get("CSPAT00701OutBlock2", {})
            new_order_id = output.get("OrdNo", "")
            
            logger.info(f"Order modified: {new_order_id}")
            return new_order_id
        
        except Exception as e:
            logger.error(f"Failed to modify order: {e}")
            raise
    
    async def cancel_order(
        self,
        account_id: str,
        order_id: str,
        symbol: str,
        quantity: int
    ) -> bool:
        """
        주문 취소 (CSPAT00801 - 현물취소)
        
        Args:
            account_id: 계좌번호
            order_id: 원주문번호
            symbol: 종목코드
            quantity: 취소수량
            
        Returns:
            취소 성공 여부
        """
        logger.info(f"Cancelling order: {order_id}")
        
        try:
            clean_account = account_id.replace("-", "")
            password = config.get("ls.account_password", "")
            
            response = await self.client.request(
                method="POST",
                endpoint="/stock/order",
                data={
                    "CSPAT00801InBlock1": {
                        "OrgOrdNo": order_id,
                        "IsuNo": symbol,
                        "OrdQty": quantity
                    }
                },
                headers={
                    "tr_id": "CSPAT00801",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 취소 성공 여부 확인 (OutBlock2에서 주문번호 확인)
            output = response.get("CSPAT00801OutBlock2", {})
            success = output.get("OrdNo", "") != ""
            
            logger.info(f"Order cancelled: {success}")
            return success
        
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    async def get_orders(self, account_id: str) -> List[LSOrder]:
        """
        주문 내역 조회 (t0425 - 주식 체결/미체결)
        
        Args:
            account_id: 계좌번호
            
        Returns:
            주문 목록
        """
        logger.info(f"Fetching orders for account: {account_id}")
        
        try:
            clean_account = account_id.replace("-", "")
            password = config.get("ls.account_password", "")
            
            # LS증권 체결/미체결 조회 API (t0425)
            response = await self.client.request(
                method="POST",
                endpoint="/stock/accno",
                data={
                    "t0425InBlock": {
                        "expcode": "",  # 종목번호 (전체 조회 시 공백)
                        "chegb": "0",  # 체결구분 (0:전체, 1:체결, 2:미체결)
                        "medosu": "0",  # 매매구분 (0:전체, 1:매도, 2:매수)
                        "sortgb": "1",  # 정렬순서 (1:주문번호 역순)
                        "cts_ordno": ""  # 연속조회 주문번호
                    }
                },
                headers={
                    "tr_id": "t0425",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 주문 내역 파싱
            orders = []
            for item in response.get("t0425OutBlock1", []):
                order = LSOrder(
                    order_id=item.get("ordno", ""),
                    account_id=account_id,
                    symbol=item.get("expcode", ""),
                    side="buy" if item.get("medosu", "") == "2" else "sell",
                    quantity=int(item.get("ordqty", 0)),
                    price=float(item.get("ordprc", 0)),
                    order_type="limit" if item.get("ordprc", 0) > 0 else "market",
                    status=self._parse_order_status(item.get("ordgb", "")),
                    filled_quantity=int(item.get("cheqty", 0)),
                    average_price=float(item.get("cheprice", 0)) if item.get("cheprice") else None,
                    created_at=datetime.now()
                )
                orders.append(order)
            
            logger.info(f"Found {len(orders)} orders")
            return orders
        
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    async def get_executions(
        self,
        account_id: str,
        order_id: str = None
    ) -> List[LSExecution]:
        """
        체결 내역 조회
        
        Args:
            account_id: 계좌번호
            order_id: 주문번호 (선택)
            
        Returns:
            체결 내역 목록
        """
        logger.info(f"Fetching executions for account: {account_id}")
        
        try:
            clean_account = account_id.replace("-", "")
            password = config.get("ls.account_password", "")
            
            # t0425에서 체결된 주문만 필터링
            response = await self.client.request(
                method="POST",
                endpoint="/stock/accno",
                data={
                    "t0425InBlock": {
                        "expcode": "",
                        "chegb": "1",  # 1:체결만
                        "medosu": "0",
                        "sortgb": "1",
                        "cts_ordno": ""
                    }
                },
                headers={
                    "tr_id": "t0425",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 체결 내역 파싱
            executions = []
            for item in response.get("t0425OutBlock1", []):
                # order_id 필터링
                if order_id and item.get("ordno", "") != order_id:
                    continue
                
                execution = LSExecution(
                    execution_id=item.get("ordno", "") + "_" + item.get("ordseq", ""),
                    order_id=item.get("ordno", ""),
                    symbol=item.get("expcode", ""),
                    side="buy" if item.get("medosu", "") == "2" else "sell",
                    quantity=int(item.get("cheqty", 0)),
                    price=float(item.get("cheprice", 0)),
                    executed_at=datetime.now()
                )
                executions.append(execution)
            
            logger.info(f"Found {len(executions)} executions")
            return executions
        
        except Exception as e:
            logger.error(f"Failed to get executions: {e}")
            raise
    
    def _parse_order_status(self, ordgb: str) -> str:
        """
        주문상태 코드를 문자열로 변환
        
        Args:
            ordgb: 주문구분 코드
            
        Returns:
            주문 상태 (pending/filled/cancelled)
        """
        status_map = {
            "1": "pending",  # 정상
            "2": "filled",  # 체결
            "3": "cancelled",  # 취소
            "4": "cancelled"  # 거부
        }
        return status_map.get(ordgb, "pending")
