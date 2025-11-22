"""
LS증권 API 응답 모델
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class LSAuthResponse(BaseModel):
    """인증 응답"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class LSOHLCData(BaseModel):
    """OHLC 데이터 응답"""
    stck_bsop_date: str = Field(..., description="영업일자")
    stck_oprc: str = Field(..., description="시가")
    stck_hgpr: str = Field(..., description="고가")
    stck_lwpr: str = Field(..., description="저가")
    stck_clpr: str = Field(..., description="종가")
    acml_vol: str = Field(..., description="누적거래량")


class LSCurrentPriceResponse(BaseModel):
    """현재가 응답"""
    stck_prpr: str = Field(..., description="현재가")
    prdy_vrss: str = Field(..., description="전일대비")
    prdy_ctrt: str = Field(..., description="전일대비율")
    acml_vol: str = Field(..., description="누적거래량")


class LSOrderResponse(BaseModel):
    """주문 응답"""
    KRX_FWDG_ORD_ORGNO: str = Field(..., description="주문조직번호")
    ODNO: str = Field(..., description="주문번호")
    ORD_TMD: str = Field(..., description="주문시각")


class LSAccountBalance(BaseModel):
    """계좌잔고 응답"""
    dnca_tot_amt: str = Field(..., description="예수금총액")
    nxdy_excc_amt: str = Field(..., description="익일정산금액")
    prvs_rcdl_excc_amt: str = Field(..., description="가수도정산금액")
    tot_evlu_amt: str = Field(..., description="총평가금액")


class LSPositionData(BaseModel):
    """보유종목 데이터"""
    pdno: str = Field(..., description="종목코드")
    prdt_name: str = Field(..., description="종목명")
    hldg_qty: str = Field(..., description="보유수량")
    pchs_avg_pric: str = Field(..., description="매입평균가격")
    prpr: str = Field(..., description="현재가")
    evlu_pfls_amt: str = Field(..., description="평가손익금액")
    evlu_pfls_rt: str = Field(..., description="평가손익율")


class LSOrderStatus(BaseModel):
    """주문체결 조회"""
    odno: str = Field(..., description="주문번호")
    ord_dt: str = Field(..., description="주문일자")
    ord_gno_brno: str = Field(..., description="주문채번지점번호")
    orgn_odno: str = Field(..., description="원주문번호")
    ord_dvsn_name: str = Field(..., description="주문구분명")
    sll_buy_dvsn_cd: str = Field(..., description="매도매수구분코드")
    pdno: str = Field(..., description="종목코드")
    ord_qty: str = Field(..., description="주문수량")
    ord_unpr: str = Field(..., description="주문단가")
    tot_ccld_qty: str = Field(..., description="총체결수량")
    tot_ccld_amt: str = Field(..., description="총체결금액")
    ord_tmd: str = Field(..., description="주문시각")
