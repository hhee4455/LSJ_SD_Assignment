from typing import List

from src.config.settings import settings
from src.utils.logging import get_logger
from src.utils.data_utils import remove_duplicates
from src.models.api_models import KISMinuteResponse, KISDailyResponse
from src.models.domain_models import MinuteData, DailyData
from src.kis.kis_auth import KISAuthManager
from src.kis.kis_client import KISAPIClient

logger = get_logger(__name__)


class StockDataExtractor:
    """삼성전자 주식 데이터 추출"""
    
    def __init__(self):
        self.auth_manager = KISAuthManager()
        self.api_client = KISAPIClient(self.auth_manager)
    
    def extract_minute_data(self) -> List[MinuteData]:
        """분봉 데이터 가져오기"""
        try:
            logger.info("분봉 데이터 추출 시작")
            
            # KIS API 호출
            raw_data = self.api_client.call_minute_api(settings.STOCK_CODE)
            
            # 데이터 변환
            response = KISMinuteResponse(**raw_data)
            minute_data_list = response.to_minute_data_list(settings.STOCK_CODE)
            
            if not minute_data_list:
                return []
            
            # 중복 제거
            unique_data = remove_duplicates(minute_data_list, lambda x: x.timestamp)
            
            logger.info(f"분봉 {len(unique_data)}건 추출 완료")
            return unique_data
            
        except Exception as e:
            logger.error(f"분봉 추출 실패: {e}")
            raise
    
    def extract_daily_data(self, start_date: str = "", end_date: str = "") -> List[DailyData]:
        """일봉 데이터 가져오기"""
        try:
            logger.info("일봉 데이터 추출 시작")
            
            # KIS API 호출
            raw_data = self.api_client.call_daily_api(settings.STOCK_CODE, start_date=start_date, end_date=end_date)
            
            # 데이터 변환
            response = KISDailyResponse(**raw_data)
            daily_data_list = response.to_daily_data_list(settings.STOCK_CODE)
            
            if not daily_data_list:
                return []
            
            # 중복 제거
            unique_data = remove_duplicates(daily_data_list, lambda x: x.date)
            
            logger.info(f"일봉 {len(unique_data)}건 추출 완료")
            return unique_data
            
        except Exception as e:
            logger.error(f"일봉 추출 실패: {e}")
            raise