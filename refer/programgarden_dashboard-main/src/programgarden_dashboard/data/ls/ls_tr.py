"""
LS Open API TR 조회 시스템
"""

from datetime import datetime
from typing import Dict, Any

from ...utils.logger import get_logger

from programgarden_finance.ls.models import SetupOptions
from programgarden_finance.ls.overseas_stock.accno import COSOQ00201
# from programgarden_finance.ls.overseas_stock.order import COSAT00301
# from programgarden_finance.ls.overseas_stock.order import COSAT00311


class LSTRProvider:
    """LS Open API TR 조회 전용 데이터 제공자"""
    
    def __init__(self):
        """LS TR 제공자 초기화"""

        # LS API 인스턴스
        self.ls_instance = None
        
        # 캐시 (단순 딕셔너리)
        self.cache = {}
        
        # 로깅
        self.logger = get_logger('LSTRProvider')
    
    # ========================================
    # LS 인스턴스 주입 및 초기화
    # ========================================
    
    def set_ls_instance(self, ls_instance):
        """
        Provider로부터 LS 인스턴스 주입받기
        
        Args:
            ls_instance: 로그인된 LS 인스턴스
            app_key: LS Open API 앱키
            app_secret: LS Open API 시크릿키
        """
        self.ls_instance = ls_instance
        
        self.logger.info("✅ LS TR Provider에 LS 인스턴스 주입 완료")
    
    # ========================================
    # TR 조회 메서드들
    # ========================================
        
    async def fetch_account_data(self) -> Dict[str, Any]:
        """
        COSOQ00201 계좌 잔고 조회 (Account 컴포넌트용)
        
        Returns:
            계좌 잔고 정보 (총 자산, 보유 종목 등)
        """
        
        # 캐시 키
        cache_key = "account_balance"
        
        try:
            date = datetime.now().strftime('%Y%m%d')
            # COSOQ00201 TR 요청
            account_tr = self.ls_instance.overseas_stock().accno().cosoq00201(
                COSOQ00201.COSOQ00201InBlock1(
                    RecCnt=1,
                    BaseDt=date,
                    CrcyCode="ALL",
                    AstkBalTpCode="00"
                ),
                options=SetupOptions(
                    on_rate_limit="wait"
                )
            )

            response = await account_tr.req_async()
            
            # 응답 데이터 변환
            account_data = self._parse_account_balance_response(response)
            
            # 캐시 저장 (10초 후 만료)
            self.cache[cache_key] = account_data

            return account_data
            
        except Exception as e:
            self.logger.error(f"❌ 계좌 잔고 TR 조회 실패: {str(e)}")
            # 빈 구조로 반환 (UI 에러 방지)
            return {
                "total_balance": 0.0,
                "available_cash": 0.0,
                "total_profit_loss": 0.0,
                "total_profit_rate": 0.0,
                "holdings": [],
                "error": str(e)
            }
    
    async def execute_order(self, 
        symbol: str, 
        order_pattern_code: str, 
        origin_order_number: int, 
        order_market_code: str, 
        order_quantity: int, 
        order_price: float,
        order_price_pattern_code: str) -> None:
        """
        매수/매도/취소 주문 요청 TR (COSAT00301)
        
        Args:
            symbol: 주식 심볼 (예: "AAPL")
            order_pattern_code: 주문 유형 코드 ("01"=매도, "02"=매수, "08"=취소)
            origin_order_number: 원주문번호 (취소 시 필요)
            order_market_code: 주문 시장 코드 ("81"=뉴욕거래소, "82"=NASDAQ)
            order_quantity: 주문 수량
            order_price: 주문 가격
            order_price_pattern_code: 주문 가격 패턴 코드 ("00"=지정가, "03"=시장가, "M1"=LOO, "M2"=LOC, "M3"=MOO, "M4"=MOC)

        Returns:
            None
        """
        # TODO 주문 메서드 구현 필요
    
    async def correct_order(self):
        """주문 정정 TR (COSAT00311)"""
    
    # ========================================
    # TR 응답 파싱 및 변환
    # ========================================
    
    def _parse_account_balance_response(self, response) -> Dict[str, Any]:
        """COSOQ00201 응답 데이터 파싱 (Pydantic 객체 구조)"""
        try:
            # Pydantic 객체로 직접 접근
            block1 = response.block1  # 계좌 기본 정보
            block2 = response.block2  # 전체 평가 요약
            block3 = response.block3  # 통화별 잔고 (리스트)
            block4 = response.block4  # 종목별 잔고 (리스트)
            
            # block2에서 전체 평가 데이터 추출
            total_balance = float(block2.WonEvalSumAmt)       # 원화평가합계금액
            available_cash = float(block2.WonDpsBalAmt)       # 원화예수금잔고금액  
            total_profit_loss = float(block2.ConvEvalPnlAmt)  # 환산평가손익금액
            total_profit_rate = float(block2.ErnRat)          # 수익율 (이미 %)
            
            # block4에서 종목별 상세 정보 추출
            holdings = []
            for stock in block4:
                holding = {
                    "symbol": stock.ShtnIsuNo,                      # 단축종목번호
                    "name": stock.JpnMktHanglIsuNm,                 # 종목명
                    "quantity": float(stock.AstkBalQty),            # 해외증권잔고수량
                    "avg_price": float(stock.FcstckUprc),           # 외화증권단가 (매수평균가)
                    "current_price": float(stock.OvrsScrtsCurpri),  # 해외증권시세 (현재가)
                    "market_value": float(stock.StkConvEvalAmt),    # 주식환산평가금액
                    "profit_loss": float(stock.ConvEvalPnlAmt),     # 환산평가손익금액
                    "profit_rate": float(stock.PnlRat),             # 손익율
                    "currency": stock.CrcyCode,                     # 통화코드
                    "market": stock.MktTpNm                         # 시장구분명
                }
                holdings.append(holding)
            
            # block3에서 통화별 잔고 정보 (추가 정보)
            currency_details = []
            for currency_info in block3:
                currency_details.append({
                    "currency": currency_info.CrcyCode,                       # 통화코드
                    "cash_balance": float(currency_info.FcurrDps),            # 외화예수금
                    "cash_eval_profit": float(currency_info.FcurrEvalPnlAmt), # 외화평가손익금액
                    "exchange_rate": float(currency_info.BaseXchrat),         # 기준환율
                    "available_amount": float(currency_info.FcurrOrdAbleAmt)  # 외화주문가능금액
                })
            
            return {
                # 기존 필드들 (block2 기반)
                "total_balance": total_balance,
                "available_cash": available_cash,
                "total_profit_loss": total_profit_loss,
                "total_profit_rate": total_profit_rate,

                # 통화별 잔고 정보 (block3 기반)
                "cash_eval_profit": currency_details[0]["cash_eval_profit"],
                "available_amount": currency_details[0]["available_amount"],
                
                # 종목 리스트 (block4 기반)
                "holdings": holdings,
                
                # 추가 정보들
                "currency_details": currency_details,  # 통화별 상세
                "account_info": {                      # 계좌 기본 정보 (block1)
                    "account_no": block1.AcntNo,
                    "base_date": block1.BaseDt
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 계좌 잔고 응답 파싱 실패: {str(e)}")
            return {
                "total_balance": 0.0,
                "cash_eval_profit": 0.0,
                "available_cash": 0.0,
                "total_profit_loss": 0.0,
                "total_profit_rate": 0.0,
                "holdings": [],
                "error": f"응답 파싱 실패: {str(e)}"
            }

    def get_cache_info(self) -> Dict:
        """캐시 정보 반환"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys())
        }
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        self.logger.info("LS TR 캐시 초기화 완료")
    
    def cleanup(self):
        """리소스 정리"""
        self.logger.info("LS TR Provider 리소스 정리 중...")
        
        # 캐시 정리
        self.cache.clear()
        
        # LS 인스턴스 정리
        if self.ls_instance:
            self.ls_instance = None
            # 필요시 logout 메서드 호출
        
        self.logger.info("✅ LS TR Provider 정리 완료")