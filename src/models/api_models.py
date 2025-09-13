from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field
from src.models.domain_models import MinuteData, DailyData
from src.config.settings import settings
from src.utils.date_utils import format_kis_date_to_iso, format_kis_datetime_to_iso


class KISMinuteItem(BaseModel):
    """KIS 분봉 개별 응답"""
    stck_bsop_date: str  # YYYYMMDD
    stck_cntg_hour: str  # HHMMSS
    stck_oprc: str       # 시가
    stck_hgpr: str       # 고가
    stck_lwpr: str       # 저가
    stck_prpr: str       # 종가
    cntg_vol: str        # 거래량

    def to_minute_data(self, stock_code: str = settings.STOCK_CODE) -> MinuteData:
        """MinuteData로 변환"""
        timestamp = format_kis_datetime_to_iso(self.stck_bsop_date, self.stck_cntg_hour)
        
        return MinuteData(
            stock_code=stock_code,
            timestamp=timestamp,
            open_price=Decimal(self.stck_oprc),
            high_price=Decimal(self.stck_hgpr),
            low_price=Decimal(self.stck_lwpr),
            close_price=Decimal(self.stck_prpr),
            volume=int(self.cntg_vol)
        )


class KISDailyItem(BaseModel):
    """KIS 일봉 개별 응답"""
    stck_bsop_date: str  # YYYYMMDD
    stck_oprc: str       # 시가
    stck_hgpr: str       # 고가
    stck_lwpr: str       # 저가
    stck_clpr: str       # 종가
    acml_vol: str        # 거래량

    def to_daily_data(self, stock_code: str = settings.STOCK_CODE) -> DailyData:
        """DailyData로 변환"""
        date = format_kis_date_to_iso(self.stck_bsop_date)
        
        return DailyData(
            stock_code=stock_code,
            date=date,
            timestamp=f"{date} 09:00:00",  # 일봉은 09:00:00으로 통일
            open_price=Decimal(self.stck_oprc),
            high_price=Decimal(self.stck_hgpr),
            low_price=Decimal(self.stck_lwpr),
            close_price=Decimal(self.stck_clpr),
            volume=int(self.acml_vol)
        )


class KISMinuteResponse(BaseModel):
    """KIS 분봉 API 응답"""
    rt_cd: str
    msg1: str
    output2: List[KISMinuteItem] = Field(default_factory=list)

    def to_minute_data_list(self, stock_code: str = settings.STOCK_CODE) -> List[MinuteData]:
        """분봉 데이터 리스트로 변환"""
        return [item.to_minute_data(stock_code) for item in self.output2]


class KISDailyResponse(BaseModel):
    """KIS 일봉 API 응답"""
    rt_cd: str
    msg1: str
    output2: List[KISDailyItem] = Field(default_factory=list)

    def to_daily_data_list(self, stock_code: str = settings.STOCK_CODE) -> List[DailyData]:
        """일봉 데이터 리스트로 변환"""
        return [item.to_daily_data(stock_code) for item in self.output2]
