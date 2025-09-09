from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from utils.datetime_utils import get_current_timestamp


class StockData(BaseModel):
    """주식 데이터 기본 클래스"""
    stock_code: str
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    created_at: str = Field(default_factory=get_current_timestamp)

    def get_base_pk(self) -> str:
        """기본 파티션 키"""
        return f"STOCK#{self.stock_code}"


class MinuteData(StockData):
    """분봉 데이터"""
    timestamp: str  # YYYY-MM-DD HH:MM:SS
    sma_5: Optional[Decimal] = None  # Transform에서 계산 후 설정
    sma_30: Optional[Decimal] = None  # Transform에서 계산 후 설정

    def get_pk(self) -> str:
        """DynamoDB 파티션 키"""
        return f"{self.get_base_pk()}#MINUTE"
    
    def get_sk(self) -> str:
        """DynamoDB 정렬 키"""
        return self.timestamp


class DailyData(StockData):
    """일봉 데이터"""
    date: str  # YYYY-MM-DD
    timestamp: str  # YYYY-MM-DD HH:MM:SS

    def get_pk(self) -> str:
        """DynamoDB 파티션 키"""
        return f"{self.get_base_pk()}#DAILY"
    
    def get_sk(self) -> str:
        """DynamoDB 정렬 키"""
        return self.date