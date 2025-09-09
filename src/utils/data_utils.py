from typing import List, Dict, Any, Union, Callable, TypeVar
from decimal import Decimal

from src.utils.logging import get_logger
from src.models.domain_models import MinuteData, DailyData, StockData

logger = get_logger(__name__)

T = TypeVar('T')


def remove_duplicates(data_list: List[T], key_func: Callable[[T], Any]) -> List[T]:
    """중복 데이터 제거 - 키 함수 기반"""
    seen = set()
    unique_data = []
    
    for item in data_list:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            unique_data.append(item)
    
    logger.info(f"중복 제거: {len(data_list)} -> {len(unique_data)}건")
    return unique_data


def sort_stock_data(data: List[Union[MinuteData, DailyData]], reverse: bool = False) -> List[Union[MinuteData, DailyData]]:
    """주식 데이터 정렬 - 분봉은 timestamp, 일봉은 date 기준"""
    if not data:
        return data
    
    # MinuteData인지 확인
    if isinstance(data[0], MinuteData):
        return sorted(data, key=lambda x: x.timestamp, reverse=reverse)
    # DailyData인지 확인
    elif isinstance(data[0], DailyData):
        return sorted(data, key=lambda x: x.date, reverse=reverse)
    else:
        logger.warning(f"알 수 없는 데이터 타입: {type(data[0])}")
        return data


def validate_stock_data(data: StockData) -> bool:
    """주식 데이터 유효성 검증 - OHLCV 논리 검증 포함"""
    try:
        # 기본 필드 검증
        if not data.stock_code:
            return False
        
        # 가격과 거래량이 양수인지 확인
        prices = [data.open_price, data.high_price, data.low_price, data.close_price]
        if any(price <= 0 for price in prices) or data.volume < 0:
            return False
        
        # OHLCV 논리 검증
        if (data.high_price < data.low_price or 
            data.high_price < max(data.open_price, data.close_price) or
            data.low_price > min(data.open_price, data.close_price)):
            return False
        
        return True
        
    except (AttributeError, TypeError):
        return False


def convert_decimal_to_string(item: Dict[str, Any], decimal_keys: List[str]) -> Dict[str, Any]:
    """Decimal 필드들을 문자열로 변환 - DynamoDB 호환성"""
    result = item.copy()
    for key in decimal_keys:
        if key in result and isinstance(result[key], Decimal):
            result[key] = str(result[key])
    return result


def to_dynamodb_item(data: Union[MinuteData, DailyData]) -> Dict[str, Any]:
    """개별 데이터를 DynamoDB 아이템으로 변환"""
    # models 활용: PK/SK 생성
    item = {
        "PK": data.get_pk(),
        "SK": data.get_sk(),
        **data.model_dump(exclude={'created_at'}),
        "created_at": data.created_at
    }
    
    # Decimal을 문자열로 변환 (DynamoDB 호환성)
    price_keys = ['open_price', 'high_price', 'low_price', 'close_price']
    item = convert_decimal_to_string(item, price_keys)
    
    # 분봉 데이터의 SMA 값도 변환
    if isinstance(data, MinuteData):
        sma_keys = ['sma_5', 'sma_30']
        item = convert_decimal_to_string(item, sma_keys)
    
    # None 값 제거
    return {k: v for k, v in item.items() if v is not None}


def to_dynamodb_items(data: List[Union[MinuteData, DailyData]]) -> List[Dict[str, Any]]:
    """여러 데이터를 DynamoDB 아이템 리스트로 변환"""
    if not data:
        return []
    
    logger.info(f"DynamoDB 아이템 변환 시작: {len(data)}건")
    items = [to_dynamodb_item(item) for item in data]
    logger.info(f"DynamoDB 아이템 변환 완료: {len(items)}건")
    
    return items
