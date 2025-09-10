from datetime import datetime
from src.config.settings import settings
from src.utils.logging import get_logger
from src.pipelines.extractor import StockDataExtractor
from src.pipelines.transformer import StockDataTransformer
from src.pipelines.loader import StockDataLoader

logger = get_logger(__name__)


def run_minute_pipeline():
    """분봉 데이터 파이프라인 실행"""
    logger.info("분봉 데이터 파이프라인 시작")
    logger.info(f"대상 종목: {settings.STOCK_CODE} (삼성전자)")
    
    try:
        # 초기화
        extractor = StockDataExtractor()
        transformer = StockDataTransformer()
        loader = StockDataLoader()
        
        # DynamoDB 연결 확인
        if not loader.health_check():
            logger.error("DynamoDB 연결 실패")
            return False
        
        # 분봉 데이터 처리 (OHLCV + SMA)
        minute_data = extractor.extract_minute_data()
        logger.info(f"분봉 데이터 추출: {len(minute_data)}건")
        
        if minute_data:
            processed_minute_data = transformer.transform_minute_data(minute_data)
            loader.save_minute_data(processed_minute_data)
            logger.info(f"분봉 데이터 저장: {len(processed_minute_data)}건 (5분SMA, 30분SMA 포함)")
        else:
            logger.info("분봉 데이터가 없습니다 (장시간 외 또는 데이터 없음)")
        
        logger.info("분봉 파이프라인 실행 완료!")
        return True
        
    except Exception as e:
        logger.error(f"분봉 파이프라인 실행 중 오류 발생: {e}")
        return False
    
    finally:
        logger.info("분봉 데이터 파이프라인 종료")


def run_daily_pipeline():
    """일봉 데이터 파이프라인 실행"""
    logger.info("일봉 데이터 파이프라인 시작")
    logger.info(f"대상 종목: {settings.STOCK_CODE} (삼성전자)")
    
    try:
        # 초기화
        extractor = StockDataExtractor()
        transformer = StockDataTransformer()
        loader = StockDataLoader()
        
        # DynamoDB 연결 확인
        if not loader.health_check():
            logger.error("DynamoDB 연결 실패")
            return False
        
        # 일봉 데이터 처리 (당일만, OHLCV)
        today = datetime.now().strftime("%Y%m%d")
        daily_data = extractor.extract_daily_data(start_date=today, end_date=today)
        logger.info(f"일봉 데이터 추출: {len(daily_data)}건")
        
        if daily_data:
            processed_daily_data = transformer.transform_daily_data(daily_data)
            loader.save_daily_data(processed_daily_data)
            logger.info(f"일봉 데이터 저장: {len(processed_daily_data)}건 (OHLCV)")
        else:
            logger.info("일봉 데이터가 없습니다 (주말/공휴일 또는 데이터 없음)")
        
        logger.info("일봉 파이프라인 실행 완료!")
        return True
        
    except Exception as e:
        logger.error(f"일봉 파이프라인 실행 중 오류 발생: {e}")
        return False
    
    finally:
        logger.info("일봉 데이터 파이프라인 종료")


def run_pipeline():
    """전체 주식 데이터 파이프라인 실행 (호환성 유지용)"""
    logger.info("전체 주식 데이터 파이프라인 시작")

    # 분봉 파이프라인 실행
    minute_success = run_minute_pipeline()
    
    # 일봉 파이프라인 실행
    daily_success = run_daily_pipeline()
    
    success = minute_success and daily_success
    logger.info(f"전체 파이프라인 실행 {'완료' if success else '실패'}!")
    
    return success


if __name__ == "__main__":
    success = run_pipeline()
    print("실행 완료" if success else "실행 실패")
