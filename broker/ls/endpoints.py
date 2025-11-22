"""
LS증권 OpenAPI 엔드포인트 정의
"""

class LSEndpoints:
    """LS증권 API 엔드포인트"""
    
    # 기본 URL (REST API는 실거래/모의투자 동일)
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    
    # OAuth
    OAUTH_TOKEN = "/oauth2/token"
    OAUTH_REVOKE = "/oauth2/revoke"
    
    # 주식 - 계좌
    STOCK_ACCOUNT = "/stock/accno"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=37d22d4d-83cd-40a4-a375-81b010a4a627
    
    # 주식 - 주문
    STOCK_ORDER = "/stock/order"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=d0e216e0-10d9-479f-8a4d-e175b8bae307
    
    # 주식 - 시세
    STOCK_MARKET = "/stock/market-data"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=54a99b02-dbba-4057-8756-9ac759c9a2ed
    
    # 주식 - 차트
    STOCK_CHART = "/stock/chart"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=12320341-ad85-429a-90bd-5b3771c5e89f
    
    # 주식 - 실시간 시세
    STOCK_REALTIME = "/stock/realtime"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=9a2800c3-9bf2-4d67-8d83-905074f06646
    
    # 주식 - 종목검색
    STOCK_SEARCH = "/stock/search"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=6b67369a-dc7a-4cc7-8c33-71bb6336b6bf
    
    # 주식 - 상위종목
    STOCK_TOP = "/stock/top"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=d3d0ef41-6a0f-4bda-9e28-160071f66206
    
    # 주식 - 투자정보
    STOCK_INFO = "/stock/info"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=580d2770-a7a9-49e3-9ec1-49ed8bc734a2
    
    # 주식 - 외인/기관
    STOCK_FOREIGN = "/stock/foreign"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=90378c39-f93e-4f95-9670-f76e5c924cc6
    
    # 주식 - 투자자
    STOCK_INVESTOR = "/stock/investor"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=c148a42f-51a7-4446-b6df-10d6056dd75b
    
    # 주식 - 프로그램
    STOCK_PROGRAM = "/stock/program"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=6b554636-7b2a-4e1a-a615-54b0c131a558
    
    # 주식 - 거래원
    STOCK_DEALER = "/stock/dealer"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=3dbce945-a73c-475c-9758-88d9922ab94e
    
    # 주식 - ETF
    STOCK_ETF = "/stock/etf"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=30b6dfd6-b0bd-4e63-a510-7d5d94edc740
    
    # 주식 - ELW
    STOCK_ELW = "/stock/elw"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=3d58c125-8b45-46b4-baf2-6f98d0373131
    
    # 주식 - 섹터
    STOCK_SECTOR = "/stock/sector"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=8f027fa6-4177-43e3-9a7a-a76873efd47c
    
    # 주식 - 기타
    STOCK_ETC = "/stock/etc"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=316495d3-6109-45a6-baaf-9e8a0261f30a
    
    # 업종 - 시세
    SECTOR_MARKET = "/sector/market-data"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=f82999f4-eb1a-4ead-a0b1-a4386e8721ab&api_id=88a7c0d3-fb4f-48ef-bc9b-4c47ac72a87b
    
    # 업종 - 차트
    SECTOR_CHART = "/sector/chart"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=f82999f4-eb1a-4ead-a0b1-a4386e8721ab&api_id=5b483d74-407c-4760-8452-1b2b1dc1dcde
    
    # 업종 - 실시간 시세
    SECTOR_REALTIME = "/sector/realtime"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=f82999f4-eb1a-4ead-a0b1-a4386e8721ab&api_id=3c2b0280-6663-41e2-8995-a179de99e074
    
    # 기타 - 시간조회
    TIME_INFO = "/time"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=6ad419a5-f0ce-47c2-a52a-91685fa86a31&api_id=3c452f0d-715e-43b5-a140-3e26f73dec76
    
    # 기타 - 실시간 시세
    ETC_REALTIME = "/etc/realtime"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=6ad419a5-f0ce-47c2-a52a-91685fa86a31&api_id=eddd61f7-d595-4370-b9c3-49c4c6178096
    
    # 실시간 시세 투자정보
    REALTIME_INFO = "/realtime/info"
    # API 문서: https://openapi.ls-sec.co.kr/apiservice?group_id=cd909627-82e5-40c9-b313-1a8fd2d7b119&api_id=d67d0790-4b26-447b-82eb-e9642f66057c
    
    # WebSocket
    WSS_URL = "wss://openapi.ls-sec.co.kr:9443/websocket"          # 실거래
    WSS_URL_PAPER = "wss://openapi.ls-sec.co.kr:29443/websocket"  # 모의투자
    
    @classmethod
    def get_wss_url(cls, paper_trading: bool = False) -> str:
        """
        WebSocket URL 반환
        
        Args:
            paper_trading: 모의투자 여부
            
        Returns:
            WebSocket URL
        """
        return cls.WSS_URL_PAPER if paper_trading else cls.WSS_URL


# API 문서 참조 링크
API_DOCS = {
    "계좌": "https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=37d22d4d-83cd-40a4-a375-81b010a4a627",
    "주문": "https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=d0e216e0-10d9-479f-8a4d-e175b8bae307",
    "시세": "https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=54a99b02-dbba-4057-8756-9ac759c9a2ed",
    "차트": "https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=12320341-ad85-429a-90bd-5b3771c5e89f",
    "실시간": "https://openapi.ls-sec.co.kr/apiservice?group_id=73142d9f-1983-48d2-8543-89b75535d34c&api_id=9a2800c3-9bf2-4d67-8d83-905074f06646",
}
