from typing import List, Optional
from collections import deque
from decimal import Decimal

from src.utils.logging import get_logger
from src.utils.data_utils import sort_stock_data
from src.models.domain_models import MinuteData, DailyData

logger = get_logger(__name__)


class StockDataTransformer:
    """주식 데이터 변환 및 정제"""
    
    def __init__(self):
        # 각각의 윈도우와 합계를 따로 관리
        self.window_5 = deque(maxlen=5)
        self.window_30 = deque(maxlen=30)
        self.sum_5 = Decimal('0')
        self.sum_30 = Decimal('0')
    
    def transform_minute_data(self, minute_data: List[MinuteData]) -> List[MinuteData]:
        """분봉 데이터 변환 - SMA 계산 포함"""
        logger.info("분봉 데이터 변환 시작")
        
        if not minute_data:
            return []
        
        # 시간순 정렬 및 SMA 계산
        sorted_data = sort_stock_data(minute_data, reverse=False)
        
        # 모든 데이터에 대해 SMA 계산
        for data in sorted_data:
            self._update_sma(data)
        
        logger.info(f"분봉 데이터 변환 완료: {len(sorted_data)}건 처리, 1건 반환 (최신 1분)")
        
        # 최신 데이터만 반환 (SMA가 계산된 상태)
        return [sorted_data[-1]] if sorted_data else []
    
    def _update_sma(self, data: MinuteData) -> None:
        """SMA 계산 로직"""
        new_price = data.close_price
        
        # 5분 SMA 업데이트
        if len(self.window_5) == 5:  # 윈도우가 가득 찬 경우
            self.sum_5 -= self.window_5[0]  # 가장 오래된 값 제거
        self.window_5.append(new_price)
        self.sum_5 += new_price
        
        # 30분 SMA 업데이트  
        if len(self.window_30) == 30:  # 윈도우가 가득 찬 경우
            self.sum_30 -= self.window_30[0]  # 가장 오래된 값 제거
        self.window_30.append(new_price)
        self.sum_30 += new_price
        
        # SMA 계산 및 설정
        if len(self.window_5) >= 5:
            data.sma_5 = self.sum_5 / len(self.window_5)
        
        if len(self.window_30) >= 30:
            data.sma_30 = self.sum_30 / len(self.window_30)

    def transform_daily_data(self, daily_data: List[DailyData]) -> List[DailyData]:
        """일봉 데이터 변환"""
        logger.info("일봉 데이터 변환 시작")
        
        if not daily_data:
            return []
        
        # 날짜순 정렬 (최신순)
        sorted_data = sort_stock_data(daily_data, reverse=True)
        
        logger.info(f"일봉 데이터 변환 완료: {len(sorted_data)}건")
        return sorted_data
