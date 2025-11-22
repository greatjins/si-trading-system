import re


class DataFormatter:
    """StockCard 데이터 포맷팅 통합 클래스"""
    
    @staticmethod
    def safe_float(value, default=0.0):
        """안전한 float 변환"""
        if not value:
            return default
        if isinstance(value, str):
            nums = re.findall(r'-?\d+\.?\d*', value)
            return float(nums[0]) if nums else default
        return float(value) if value else default
    
    @classmethod
    def price(cls, data, field='price'):
        """가격 포맷팅"""
        if not isinstance(data, dict):
            return '$0.00'
        value = cls.safe_float(data.get(field, 0))
        return f'${value:.2f}'
    
    @classmethod  
    def volume(cls, data, field='volume'):
        """거래량 포맷팅"""
        if not isinstance(data, dict):
            return '0'
        vol = int(cls.safe_float(data.get(field, 0)))
        if vol >= 1_000_000:
            return f'{vol/1_000_000:.1f}M'
        elif vol >= 1_000:
            return f'{vol/1_000:.1f}K'
        return f'{vol:,}'
    
    @classmethod
    def change(cls, data, field='change', percent_field='change_percent'):
        """변동 포맷팅"""
        if not isinstance(data, dict):
            return '$0.00 (0.00%)'
        change = cls.safe_float(data.get(field, 0))
        change_percent = cls.safe_float(data.get(percent_field, 0))
        sign = '+' if change > 0 else '-' if change < 0 else ''
        return f'{sign}${change:.2f} ({change_percent:+.2f}%)'
    
    @classmethod
    def amount(cls, data, field='amount'):
        """거래대금 포맷팅"""
        if not isinstance(data, dict):
            return '$0'
        amt = int(cls.safe_float(data.get(field, 0)))
        if amt >= 1_000_000_000:
            return f'${amt/1_000_000_000:.1f}B'
        elif amt >= 1_000_000:
            return f'${amt/1_000_000:.1f}M'
        return f'${amt:,}'
    
    @classmethod
    def source(cls, data, field='source'):
        """데이터 소스 포맷팅"""
        if not isinstance(data, dict):
            return '연결중...'
        source = data.get(field, '연결중...')
        return str(source).replace('(Mock)', '') if source else '연결중...'
    
    @classmethod
    def range_52week(cls, data):
        """52주 범위 포맷팅"""
        if not isinstance(data, dict):
            return '$0.00-$0.00'
        high52 = cls.safe_float(data.get('high52', 0))
        low52 = cls.safe_float(data.get('low52', 0))
        if high52 > 0 and low52 > 0:
            return f'${low52:.2f}-${high52:.2f}'
        return '$0.00-$0.00'
    
    @classmethod
    def range_52week_percent(cls, data):
        """52주 범위 내 현재가 위치 백분율"""
        if not isinstance(data, dict):
            return '0%'
        price = cls.safe_float(data.get('price', 0))
        high52 = cls.safe_float(data.get('high52', 0))
        low52 = cls.safe_float(data.get('low52', 0))
        if high52 > low52 > 0 and price > 0:
            try:
                percent = ((price - low52) / (high52 - low52)) * 100
                return f'{percent:.0f}%'
            except ZeroDivisionError:
                return '0%'
        return '0%'
    
    @classmethod
    def trdq(cls, data, field='trdq'):
        """건별체결수량 포맷팅"""
        if not isinstance(data, dict):
            return '0'
        trdq = int(cls.safe_float(data.get(field, 0)))
        if trdq >= 1_000_000:
            return f'{trdq/1_000_000:.1f}M'
        elif trdq >= 1_000:
            return f'{trdq/1_000:.1f}K'
        return f'{trdq:,}'
    
    @classmethod
    def cgubun_icon_name(cls, data):
        """체결구분 아이콘 이름 반환"""
        if not isinstance(data, dict):
            return 'trending_flat'
        cgubun = str(data.get('cgubun', '')).strip()
        if cgubun == '+':
            return 'trending_up'      # 매수 우세
        elif cgubun == '-':
            return 'trending_down'    # 매도 우세
        else:
            return 'trending_flat'    # 보합
    
    @classmethod
    def cgubun_icon_color(cls, data):
        """체결구분 아이콘 색상 클래스 반환"""
        if not isinstance(data, dict):
            return 'text-gray-400'
        cgubun = str(data.get('cgubun', '')).strip()
        if cgubun == '+':
            return 'text-green-500'   # 매수 우세
        elif cgubun == '-':
            return 'text-red-500'     # 매도 우세
        else:
            return 'text-gray-400'    # 보합