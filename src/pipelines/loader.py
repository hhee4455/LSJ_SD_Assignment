from typing import List, Dict, Any, Union
import boto3
from botocore.exceptions import ClientError
import time

from src.config.settings import settings
from src.utils.logging import get_logger
from src.utils.data_utils import to_dynamodb_items, validate_stock_data, remove_duplicates
from src.utils.retry import retry_with_delay
from src.models.domain_models import MinuteData, DailyData

logger = get_logger(__name__)


class DynamoDBLoader:
    """DynamoDB 데이터 저장"""
    
    # AWS DynamoDB 제약사항
    BATCH_SIZE = 25
    
    def __init__(self, table_name: str = None):
        self.table_name = table_name or settings.DYNAMODB_TABLE_NAME
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"DynamoDBLoader 초기화 - 테이블: {self.table_name}")
    
    def save_data(self, data: List[Union[MinuteData, DailyData]]) -> bool:
        """데이터 저장"""
        if not data:
            logger.warning("저장할 데이터가 없습니다")
            return True
        
        # 중복 제거
        if isinstance(data[0], MinuteData):
            clean_data = remove_duplicates(data, key_func=lambda x: x.timestamp)
        else:
            clean_data = remove_duplicates(data, key_func=lambda x: x.date)
        
        # 데이터 검증
        valid_data = [item for item in clean_data if validate_stock_data(item)]
        
        if not valid_data:
            logger.error("유효한 데이터가 없습니다")
            return False
        
        logger.info(f"데이터 정제 완료: {len(data)} -> {len(valid_data)}건")
        
        # DynamoDB 아이템 변환
        items = to_dynamodb_items(valid_data)
        
        # 배치 저장
        return self._batch_save(items)
    
    @retry_with_delay(exceptions=(ClientError,))
    def _batch_save(self, items: List[Dict[str, Any]]) -> bool:
        """배치 저장 - AWS 제약사항 처리"""
        try:
            total_items = len(items)
            
            # 25개씩 배치 처리
            for i in range(0, total_items, self.BATCH_SIZE):
                batch = items[i:i + self.BATCH_SIZE]
                batch_num = (i // self.BATCH_SIZE) + 1
                total_batches = (total_items + self.BATCH_SIZE - 1) // self.BATCH_SIZE
                
                logger.info(f"배치 {batch_num}/{total_batches} 저장 중 ({len(batch)}건)")
                
                # DynamoDB 배치 저장
                with self.table.batch_writer() as batch_writer:
                    for item in batch:
                        batch_writer.put_item(Item=item)
                
                # 요청 제한 방지
                if i + self.BATCH_SIZE < total_items:
                    time.sleep(0.1)
            
            logger.info(f"전체 배치 저장 완료: {total_items}건")
            return True
            
        except ClientError as e:
            logger.error(f"DynamoDB 저장 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            return False
    
    def get_recent_data(self, stock_code: str, data_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 데이터 조회"""
        try:
            # 기본 종목코드
            stock_code = stock_code or settings.STOCK_CODE
            
            # PK 생성 규칙
            if data_type.upper() in ['MINUTE', '분봉']:
                pk = f"STOCK#{stock_code}#MINUTE"
            elif data_type.upper() in ['DAILY', '일봉']:
                pk = f"STOCK#{stock_code}#DAILY"
            else:
                logger.error(f"지원하지 않는 데이터 타입: {data_type}")
                return []
            
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq(pk),
                ScanIndexForward=False,  # 최신순
                Limit=limit
            )
            
            items = response.get('Items', [])
            logger.info(f"{data_type} 최근 데이터 {len(items)}건 조회")
            return items
            
        except ClientError as e:
            logger.error(f"데이터 조회 실패: {e}")
            return []
    
    def health_check(self) -> bool:
        """DynamoDB 연결 상태 확인"""
        try:
            self.table.meta.client.describe_table(TableName=self.table_name)
            logger.info(f"DynamoDB 테이블 '{self.table_name}' 연결 정상")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"테이블 '{self.table_name}'을 찾을 수 없습니다")
            else:
                logger.error(f"DynamoDB 연결 오류: {e}")
            return False


class StockDataLoader:
    """주식 데이터 로더"""
    
    def __init__(self, table_name: str = None):
        self.loader = DynamoDBLoader(table_name)
        logger.info("StockDataLoader 초기화 완료")
    
    def save_minute_data(self, minute_data: List[MinuteData]) -> bool:
        """분봉 데이터 저장 (OHLCV + SMA)"""
        logger.info(f"분봉 데이터 저장 요청: {len(minute_data)}건")
        return self.loader.save_data(minute_data)
    
    def save_daily_data(self, daily_data: List[DailyData]) -> bool:
        """일봉 데이터 저장 (OHLCV)"""
        logger.info(f"일봉 데이터 저장 요청: {len(daily_data)}건")
        return self.loader.save_data(daily_data)
    
    def get_recent_data(self, data_type: str = "MINUTE", limit: int = 10) -> List[Dict[str, Any]]:
        """최근 데이터 조회 - config의 기본 종목코드 사용"""
        return self.loader.get_recent_data(settings.STOCK_CODE, data_type, limit)
    
    def health_check(self) -> bool:
        """로더 상태 확인"""
        return self.loader.health_check()
