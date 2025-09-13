from typing import List
from collections import deque
from decimal import Decimal

from src.utils.logging import get_logger
from src.utils.data_utils import sort_stock_data
from src.models.domain_models import MinuteData, DailyData

logger = get_logger(__name__)


class StockDataTransformer:
    """주식 데이터 변환 및 정제"""
    
    def __init__(self):
        # 슬라이딩 윈도우 (최근 30개 가격만 저장)
        self.price_window = deque(maxlen=30)
        self.window_sum = Decimal('0')
        self.initialized = False  # 초기화 상태 추적
    
    def transform_minute_data(self, minute_data: List[MinuteData]) -> List[MinuteData]:
        """분봉 데이터 변환 - SMA 계산 포함"""
        logger.info("분봉 데이터 변환 시작")
        
        if not minute_data:
            return []
        
        # 시간순 정렬 및 SMA 계산
        sorted_data = sort_stock_data(minute_data, reverse=False)
        
        if not self.initialized:
            # 전체 데이터로 윈도우 초기화
            for data in sorted_data:
                self._update_sma_efficiently(data)
            self.initialized = True
            
            # 최신 데이터 반환 (SMA 포함)
            return [sorted_data[-1]] if sorted_data else []
        else:
            # 이후 호출: 최신 1개만 처리
            if sorted_data:
                latest_data = sorted_data[-1]
                self._update_sma_efficiently(latest_data)
                return [latest_data]
            return []
    
    def _update_sma_efficiently(self, data: MinuteData) -> MinuteData:
        """SMA 계산 로직"""
        new_price = data.close_price
        
        # 윈도우가 가득 찬 경우 가장 오래된 값 제거
        if len(self.price_window) == 30:
            self.window_sum -= self.price_window[0]
        
        # 새 값 추가
        self.price_window.append(new_price)
        self.window_sum += new_price
        
        # SMA 계산 
        window_len = len(self.price_window)
        if window_len >= 5:
            data.sma_5 = sum(list(self.price_window)[-5:]) / 5
        if window_len >= 30:
            data.sma_30 = self.window_sum / 30
        
        return data
    
    def transform_daily_data(self, daily_data: List[DailyData]) -> List[DailyData]:
        """일봉 데이터 변환"""
        logger.info("일봉 데이터 변환 시작")
        
        if not daily_data:
            return []
        
        # 날짜순 정렬 (최신순)
        sorted_data = sort_stock_data(daily_data, reverse=True)
        
        logger.info(f"일봉 데이터 변환 완료: {len(sorted_data)}건")
        return sorted_data
