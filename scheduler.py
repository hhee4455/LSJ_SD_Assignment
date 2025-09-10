from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from main import run_pipeline
from src.utils.logging import get_logger
from src.utils.date_utils import is_trading_time, get_market_status

logger = get_logger(__name__)


def minute_job():
    """1분봉 데이터 수집"""
    current_time = datetime.now()

    # 거래시간 체크
    if not is_trading_time(current_time):
        # 매 시간 정각에만 상태 메시지 출력
        if current_time.minute == 0:
            status = get_market_status(current_time)
            logger.info(f"장이 닫혀 있습니다 ({status})")
        return
    
    try:
        # 모든 하위 로그 완전히 숨김
        logging.getLogger().setLevel(logging.CRITICAL)
        
        success = run_pipeline()
        
        # 로그 레벨 복원
        logging.getLogger().setLevel(logging.INFO)
        
        if success:
            logger.info(f"[{current_time.strftime('%H:%M')}] 1분봉 수집 완료")
        else:
            logger.error(f"[{current_time.strftime('%H:%M')}] 1분봉 수집 실패")
    except Exception as e:
        logging.getLogger().setLevel(logging.INFO)
        logger.error(f"[{current_time.strftime('%H:%M')}] 오류: {str(e)[:50]}...")


def daily_job():
    """일봉 데이터 수집"""
    current_time = datetime.now()
    
    # 거래일 체크
    status = get_market_status(current_time)
    if "휴장일" in status:
        logger.info(f"장이 닫혀 있습니다 ({status})")
        return
    
    try:
        # 모든 하위 로그 완전히 숨김
        logging.getLogger().setLevel(logging.CRITICAL)
        
        success = run_pipeline()
        
        # 로그 레벨 복원
        logging.getLogger().setLevel(logging.INFO)
        
        if success:
            logger.info(f"[{current_time.strftime('%H:%M')}] 일봉 수집 완료")
        else:
            logger.error(f"[{current_time.strftime('%H:%M')}] 일봉 수집 실패")
    except Exception as e:
        logging.getLogger().setLevel(logging.INFO)
        logger.error(f"[{current_time.strftime('%H:%M')}] 오류: {str(e)[:50]}...")


def main():
    """스케줄러 실행"""
    # 모든 라이브러리 로깅 완전히 숨김
    logging.getLogger('apscheduler').setLevel(logging.CRITICAL)
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    
    scheduler = BlockingScheduler()
    
    # 1분봉 수집 (9시-15시30분)
    scheduler.add_job(
        minute_job,
        CronTrigger(
            day_of_week='mon-sun',
            hour='8-16',
            minute='*',
            second=0
        ),
        id='minute_collection',
        max_instances=1
    )
    
    # 일봉 수집 (16시)
    scheduler.add_job(
        daily_job,
        CronTrigger(
            day_of_week='mon-sun',
            hour=16,
            minute=0,
            second=0
        ),
        id='daily_collection',
        max_instances=1
    )
    
    logger.info("스케줄러 시작 - 1분봉(09:00-15:30), 일봉(16:00)")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("스케줄러 종료")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
