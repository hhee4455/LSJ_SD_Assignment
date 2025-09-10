from typing import List

from src.utils.logging import get_logger
from src.utils.data_utils import sort_stock_data
from src.models.domain_models import MinuteData, DailyData

logger = get_logger(__name__)


class StockDataTransformer:
    """주식 데이터 변환 및 정제"""
    
    def transform_minute_data(self, minute_data: List[MinuteData]) -> List[MinuteData]:
        """분봉 데이터 변환 - SMA 계산 포함"""
        logger.info("분봉 데이터 변환 시작")
        
        if not minute_data:
            return []
        
        # 시간순 정렬 및 SMA 계산
        sorted_data = sort_stock_data(minute_data, reverse=False)
        self._calculate_sma(sorted_data)
        
        logger.info(f"분봉 데이터 변환 완료: {len(sorted_data)}건")
        return sorted_data
    
    def transform_daily_data(self, daily_data: List[DailyData]) -> List[DailyData]:
        """일봉 데이터 변환"""
        logger.info("일봉 데이터 변환 시작")
        
        if not daily_data:
            return []
        
        # 날짜순 정렬 (최신순)
        sorted_data = sort_stock_data(daily_data, reverse=True)
        
        logger.info(f"일봉 데이터 변환 완료: {len(sorted_data)}건")
        return sorted_data
    
    def _calculate_sma(self, data: List[MinuteData]) -> None:
        """SMA(Simple Moving Average) 계산"""
        if not data:
            return
        
        data_len = len(data)
        logger.info(f"SMA 계산 시작: {data_len}건")
        
        # 5분 SMA 계산
        self._calculate_sma_window(data, window_size=5, attr_name='sma_5')
        
        # 30분 SMA 계산  
        self._calculate_sma_window(data, window_size=30, attr_name='sma_30')
        
        logger.info("SMA 계산 완료")
    
    def _calculate_sma_window(self, data: List[MinuteData], window_size: int, attr_name: str) -> None:
        """SMA 계산"""
        data_len = len(data)
        
        if data_len < window_size:
            # 데이터가 윈도우 크기보다 작으면 누적 평균 계산
            for i in range(data_len):
                current_window = data[:i + 1]
                avg_price = sum(item.close_price for item in current_window) / len(current_window)
                setattr(data[i], attr_name, avg_price)
            return
        
        # 첫 번째 윈도우의 합계 계산
        window_sum = sum(data[j].close_price for j in range(window_size))
        setattr(data[window_size - 1], attr_name, window_sum / window_size)
        
        # 슬라이딩 윈도우로 나머지 계산 (O(n) 복잡도)
        for i in range(window_size, data_len):
            # 이전 값 제거, 새 값 추가
            window_sum = window_sum - data[i - window_size].close_price + data[i].close_price
            setattr(data[i], attr_name, window_sum / window_size)
        
        # 초기 데이터들의 SMA (윈도우 크기보다 작은 구간)
        for i in range(window_size - 1):
            current_window = data[:i + 1]
            avg_price = sum(item.close_price for item in current_window) / len(current_window)
            setattr(data[i], attr_name, avg_price)
