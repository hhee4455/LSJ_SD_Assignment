from typing import List, Dict, Any, Union, Callable, TypeVar
from decimal import Decimal

from utils.logging import get_logger
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
    
    return unique_data


def sort_stock_data(data: List[Union[MinuteData, DailyData]], reverse: bool = False) -> List[Union[MinuteData, DailyData]]:
    """주식 데이터 정렬 - 분봉은 timestamp, 일봉은 date 기준"""
    if not data:
        return data
    
    # 첫 번째 데이터 타입 확인
    first_item = data[0]
    
    # MinuteData인지 확인 (timestamp 속성 존재)
    if hasattr(first_item, 'timestamp') and hasattr(first_item, 'sma_5'):
        return sorted(data, key=lambda x: x.timestamp, reverse=reverse)
    # DailyData인지 확인 (date 속성 존재)
    elif hasattr(first_item, 'date') and not hasattr(first_item, 'sma_5'):
        return sorted(data, key=lambda x: x.date, reverse=reverse)


def validate_stock_data(data: StockData) -> bool:
    """개별 주식 데이터 유효성 검증"""
    # 기본 필드 검증
    if not data.stock_code or any(price < 0 for price in [
        data.open_price, data.high_price, data.low_price, data.close_price
    ]) or data.volume < 0:
        logger.error(f"기본 필드 검증 실패: {data.stock_code}")
        return False
    
    # 가격 논리 검증 (고가 >= 저가, 고가 >= 시가/종가, 저가 <= 시가/종가)
    if (data.high_price < data.low_price or 
        data.high_price < max(data.open_price, data.close_price) or
        data.low_price > min(data.open_price, data.close_price)):
        logger.error(f"가격 논리 검증 실패: {data.stock_code}")
        return False
    
    return True


def validate_data_quality(data: List[Union[MinuteData, DailyData]]) -> bool:
    """데이터 품질 검증 - 리스트 전체 검증"""
    if not data:
        logger.warning("검증할 데이터가 없습니다")
        return False
    
    try:
        for item in data:
            if not validate_stock_data(item):
                return False
        
        logger.info(f"데이터 품질 검증 통과: {len(data)}건")
        return True
        
    except Exception as e:
        logger.error(f"데이터 품질 검증 실패: {e}")
        return False


def convert_decimal_to_string(item: Dict[str, Any], decimal_keys: List[str]) -> Dict[str, Any]:
    """Decimal 필드들을 문자열로 변환"""
    result = item.copy()
    for key in decimal_keys:
        if key in result and isinstance(result[key], Decimal):
            result[key] = str(result[key])
    return result


def to_dynamodb_item(data: Union[MinuteData, DailyData]) -> Dict[str, Any]:
    """개별 데이터를 DynamoDB 아이템으로 변환"""
    # 기본 아이템 생성 - 모델의 dict() 메서드 활용
    item = {
        "PK": data.get_pk(),
        "SK": data.get_sk(),
        **data.dict(exclude={'created_at'}),  # created_at은 별도 처리
        "created_at": data.created_at
    }
    
    # Decimal을 문자열로 변환
    item = convert_decimal_to_string(item, ['open_price', 'high_price', 'low_price', 'close_price'])
    
    # SMA 값도 문자열로 변환 (분봉 데이터인 경우)
    if isinstance(data, MinuteData):
        item['sma_5'] = str(data.sma_5) if data.sma_5 else None
        item['sma_30'] = str(data.sma_30) if data.sma_30 else None
    
    # None 값 제거
    return {k: v for k, v in item.items() if v is not None}


def to_dynamodb_items(data: List[Union[MinuteData, DailyData]]) -> List[Dict[str, Any]]:
    """여러 데이터를 DynamoDB 아이템 리스트로 변환"""
    logger.info("DynamoDB 아이템 변환 시작")
    
    items = [to_dynamodb_item(item) for item in data]
    
    logger.info(f"DynamoDB 아이템 변환 완료: {len(items)}건")
    return items
