from src.config.settings import settings
from src.utils.logging import get_logger
from src.pipelines.extractor import StockDataExtractor
from src.pipelines.transformer import StockDataTransformer
from src.pipelines.loader import StockDataLoader

logger = get_logger(__name__)


def run_pipeline():
    """데이터 파이프라인 실행"""
    logger.info("=== 주식 데이터 파이프라인 시작 ===")
    logger.info(f"대상 종목: {settings.STOCK_CODE} (삼성전자)")
    
    try:
        # 1. 데이터 추출 (Extractor)
        logger.info("1단계: 데이터 추출")
        extractor = StockDataExtractor()
        
        # 분봉 데이터 추출
        minute_data = extractor.extract_minute_data()
        logger.info(f"분봉 데이터 추출: {len(minute_data)}건")
        
        # 일봉 데이터 추출
        daily_data = extractor.extract_daily_data()
        logger.info(f"일봉 데이터 추출: {len(daily_data)}건")
        
        # 2. 데이터 변환 (Transformer)
        logger.info("2단계: 데이터 변환")
        transformer = StockDataTransformer()
        
        # 분봉 데이터 변환 (SMA 계산 포함)
        if minute_data:
            processed_minute_data = transformer.transform_minute_data(minute_data)
            logger.info(f"분봉 데이터 변환 완료: SMA 계산 포함")
        else:
            processed_minute_data = []
        
        # 일봉 데이터 변환
        if daily_data:
            processed_daily_data = transformer.transform_daily_data(daily_data)
            logger.info(f"일봉 데이터 변환 완료")
        else:
            processed_daily_data = []
        
        # 3. 데이터 저장 (Loader)
        logger.info("3단계: 데이터 저장")
        loader = StockDataLoader()
        
        # DynamoDB 연결 확인
        if not loader.health_check():
            logger.error("DynamoDB 연결 실패. 테이블을 먼저 설정해주세요.")
            logger.error("python setup_dynamodb.py 를 실행하세요.")
            return False
        
        # 분봉 데이터 저장 (OHLCV + SMA)
        if processed_minute_data:
            minute_success = loader.save_minute_data(processed_minute_data)
            logger.info(f"분봉 데이터 저장: {'성공' if minute_success else '실패'}")
        else:
            minute_success = True
            logger.info("저장할 분봉 데이터가 없습니다")
        
        # 일봉 데이터 저장 (OHLCV)
        if processed_daily_data:
            daily_success = loader.save_daily_data(processed_daily_data)
            logger.info(f"일봉 데이터 저장: {'성공' if daily_success else '실패'}")
        else:
            daily_success = True
            logger.info("저장할 일봉 데이터가 없습니다")
        
        # 결과 확인
        if minute_success and daily_success:
            logger.info("파이프라인 실행 완료!")
            
            # 저장된 데이터 확인
            recent_minute = loader.get_recent_data("MINUTE", 5)
            recent_daily = loader.get_recent_data("DAILY", 5)
            
            logger.info(f"📊 저장 확인 - 최근 분봉: {len(recent_minute)}건, 최근 일봉: {len(recent_daily)}건")
            return True
        else:
            logger.error("파이프라인 실행 실패")
            return False
            
    except Exception as e:
        logger.error(f"파이프라인 실행 중 오류 발생: {e}")
        return False
    
    finally:
        logger.info("=== 주식 데이터 파이프라인 종료 ===")


def main():
    success = run_pipeline()
    
    if success:
        print("DynamoDB에서 데이터를 확인해보세요.")
    else:
        print("로그를 확인하고 설정을 점검해주세요.")


if __name__ == "__main__":
    main()
