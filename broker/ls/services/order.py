"""
LS증권 주문 서비스
"""
import asyncio
from typing import Optional, List
from datetime import datetime

from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type
)
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
        price: Optional[float] = None,
        mbr_no: str = "KRX"
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
            mbr_no: 회원사번호 (KRX 또는 NXT, 기본값: KRX)
            
        Returns:
            주문번호
        """
        logger.info(f"Placing order: {side} {quantity} {symbol} @ {price} (MbrNo: {mbr_no})")
        
        # 리스크 관리: 주문 수량 및 가격 검증
        if quantity <= 0:
            error_msg = f"주문 수량이 0 이하입니다. 수량: {quantity}, 종목: {symbol}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 지정가 주문인 경우 가격 검증
        if order_type.lower() == "limit":
            if price is None:
                error_msg = f"지정가 주문인데 가격이 없습니다. 종목: {symbol}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            if price <= 0:
                error_msg = f"주문 가격이 비정상적입니다. 가격: {price}, 종목: {symbol}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            # 가격이 너무 높은 경우도 체크 (예: 1억원 이상)
            if price > 100_000_000:
                error_msg = f"주문 가격이 비정상적으로 높습니다. 가격: {price:,.0f}, 종목: {symbol}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # 재시도 로직이 포함된 내부 함수
        return await self._place_order_with_retry(
            account_id, symbol, side, quantity, order_type, price, mbr_no
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.5),
        retry=retry_if_exception_type((ValueError, ConnectionError, TimeoutError, asyncio.TimeoutError))
    )
    async def _place_order_with_retry(
        self,
        account_id: str,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str,
        price: Optional[float],
        mbr_no: str
    ) -> str:
        """
        재시도 로직이 포함된 주문 실행 내부 함수
        
        Args:
            account_id: 계좌번호
            symbol: 종목코드
            side: 매수/매도 (buy/sell)
            quantity: 수량
            order_type: 주문 유형 (limit/market)
            price: 가격 (지정가 주문 시)
            mbr_no: 회원사번호 (KRX 또는 NXT)
            
        Returns:
            주문번호
        """
        try:
            # 계좌번호에서 "-" 제거
            clean_account = account_id.replace("-", "")
            
            # 계좌 비밀번호
            password = config.get("ls.account_password", "")
            
            # 매수/매도 구분 (1:매도, 2:매수)
            buy_sell_gb = "2" if side.lower() == "buy" else "1"
            
            # 주문 유형 (00:지정가, 03:시장가, 12:중간가)
            order_type_code = "03" if order_type.lower() == "market" else "00"
            
            # 넥스트레이드 전용 주문 확인
            if mbr_no == "NXT" and order_type_code == "12":
                logger.info(f"넥스트레이드 전용 주문: {symbol} (중간가 호가)")
            
            # 주문 가격 (시장가는 0)
            order_price = 0 if order_type.lower() == "market" else int(price)
            
            # LS증권 현물주문 API (CSPAT00601)
            # MbrNo 필드: 현재 시간에 따라 "KRX" 또는 "NXT"를 결정하여 전달
            # - KRX: 한국거래소 (09:00 ~ 15:30 정규장)
            # - NXT: 넥스트레이드 (08:00 ~ 08:50 장전 시간외)
            # ExecutionEngine.determine_market()에서 결정된 값이 Order.metadata를 통해 전달됨
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
                        "MgntrnCode": "000",  # 신용거래코드 (000:보통)
                        "LoanDt": "",  # 대출일
                        "OrdCndiTpCode": "0",  # 주문조건구분 (0:없음)
                        "MbrNo": mbr_no  # 회원사번호 (KRX 또는 NXT) - ExecutionEngine.determine_market()에서 결정
                    }
                },
                headers={
                    "tr_id": "CSPAT00601",
                    "tr_cont": "N",
                    "custtype": "P"
                }
            )
            
            # 응답 구조 확인을 위한 디버깅
            logger.debug(f"Place order response: {response}")
            
            # 에러 응답 확인 (rsp_cd, rsp_msg가 있는 경우)
            if "rsp_cd" in response or "rsp_msg" in response:
                rsp_cd = response.get("rsp_cd", "")
                rsp_msg = response.get("rsp_msg", "알 수 없는 오류")
                
                # 응답 코드가 "00000"이 아니면 에러 (재시도 가능)
                if rsp_cd and rsp_cd != "00000":
                    error_msg = f"주문 실패 (코드: {rsp_cd}): {rsp_msg}"
                    logger.warning(f"Order placement failed (재시도 가능): {error_msg}")
                    raise ValueError(error_msg)
            
            # 주문번호는 CSPAT00601OutBlock2에 있음 (API 문서 참조)
            output = response.get("CSPAT00601OutBlock2", {})
            
            # 다른 가능한 응답 구조 시도 (하위 호환성)
            if not output:
                output = response.get("CSPAT00601OutBlock1", {})
            if not output:
                output = response.get("output", {})
            if not output:
                output = response.get("CSPAT00601OutBlock", {})
            
            # 배열인 경우 첫 번째 요소 사용
            if isinstance(output, list) and len(output) > 0:
                output = output[0]
            
            # 주문번호 추출 (OrdNo는 CSPAT00601OutBlock2에 있음)
            order_id = (
                output.get("OrdNo") or 
                output.get("ODNO") or 
                output.get("ordno") or 
                output.get("ORDNO") or
                output.get("odno") or
                ""
            )
            
            if not order_id:
                # 응답 전체를 로깅하여 구조 확인
                logger.warning(f"Order ID not found in response. Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                logger.warning(f"Response: {response}")
                logger.warning(f"Output keys: {list(output.keys()) if isinstance(output, dict) else 'Not a dict'}")
                logger.warning(f"Full output: {output}")
                
                # 에러 메시지가 있으면 포함
                if "rsp_msg" in response:
                    error_msg = f"주문번호를 찾을 수 없습니다. API 응답: {response.get('rsp_msg', '알 수 없는 오류')}"
                else:
                    error_msg = "주문번호를 찾을 수 없습니다. API 응답 구조를 확인하세요."
                
                raise ValueError(error_msg)
            
            logger.info(f"Order placed: {order_id}")
            return order_id
        
        except asyncio.TimeoutError as e:
            logger.warning(f"주문 제출 타임아웃 (재시도 가능): {e}")
            raise
        except ConnectionError as e:
            logger.warning(f"네트워크 오류 (재시도 가능): {e}")
            raise
        except ValueError as e:
            # ValueError는 재시도 가능한 경우와 불가능한 경우가 있음
            # 이미 검증 단계에서 발생한 ValueError는 재시도하지 않음
            # API 응답에서 발생한 ValueError는 재시도 가능
            error_str = str(e)
            if "주문 실패" in error_str or "주문번호를 찾을 수 없습니다" in error_str:
                # API 응답 에러는 재시도 가능
                raise
            else:
                # 검증 에러는 재시도 불가능
                logger.error(f"주문 검증 실패 (재시도 불가): {e}")
                raise
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
            from broker.ls.models.order import OrderSide, OrderType, OrderStatus
            
            orders = []
            for item in response.get("t0425OutBlock1", []):
                # Enum 변환
                side_enum = OrderSide.BUY if item.get("medosu", "") == "2" else OrderSide.SELL
                order_type_enum = OrderType.LIMIT if item.get("ordprc", 0) > 0 else OrderType.MARKET
                status_str = self._parse_order_status(item.get("ordgb", ""))
                status_enum = OrderStatus.PENDING
                if status_str == "filled":
                    status_enum = OrderStatus.FILLED
                elif status_str == "cancelled":
                    status_enum = OrderStatus.CANCELLED
                
                order = LSOrder(
                    order_id=item.get("ordno", ""),
                    account_id=account_id,
                    symbol=item.get("expcode", ""),
                    name=item.get("hname", ""),  # 종목명
                    side=side_enum,
                    order_type=order_type_enum,
                    quantity=int(item.get("ordqty", 0)),
                    price=float(item.get("ordprc", 0)) if item.get("ordprc", 0) > 0 else None,
                    filled_quantity=int(item.get("cheqty", 0)),
                    remaining_quantity=int(item.get("ordqty", 0)) - int(item.get("cheqty", 0)),
                    filled_price=float(item.get("cheprice", 0)) if item.get("cheprice") else None,
                    status=status_enum,
                    order_time=datetime.now(),  # TODO: 실제 주문 시간 파싱
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
