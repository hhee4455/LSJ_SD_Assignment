from typing import List

from utils.logging import get_logger
from utils.data_utils import sort_stock_data
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
        """SMA(Simple Moving Average) 계산 - 원본 데이터를 직접 수정"""
        for i, item in enumerate(data):
            # 5분 SMA: 최근 5개 데이터 평균
            sma_5_values = [data[j].close_price for j in range(max(0, i - 4), i + 1)]
            item.sma_5 = sum(sma_5_values) / len(sma_5_values)
            
            # 30분 SMA: 최근 30개 데이터 평균
            sma_30_values = [data[j].close_price for j in range(max(0, i - 29), i + 1)]
            item.sma_30 = sum(sma_30_values) / len(sma_30_values)
        
        logger.info("SMA 계산 완료")
