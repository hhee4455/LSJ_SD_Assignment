from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from main import run_pipeline
from src.config.settings import settings
from src.utils.logging import get_logger
from src.utils.date_utils import get_market_status

logger = get_logger(__name__)


def minute_job():
    """1분봉 데이터 수집"""
    current_time = datetime.now()
    
    try:
        # 하위 로그 레벨 조정
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)
        
        success = run_pipeline()
        
        # 로그 레벨 복원
        logging.getLogger().setLevel(original_level)
        
        if success:
            logger.info(f"[{current_time.strftime('%H:%M')}] 1분봉 수집 완료")
        else:
            logger.error(f"[{current_time.strftime('%H:%M')}] 1분봉 수집 실패")
    except Exception as e:
        logging.getLogger().setLevel(original_level)
        logger.error(f"[{current_time.strftime('%H:%M')}] 오류: {str(e)[:50]}...")


def daily_job():
    """일봉 데이터 수집"""
    current_time = datetime.now()
    
    try:
        # 하위 로그 레벨 조정
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)
        
        success = run_pipeline()
        
        # 로그 레벨 복원
        logging.getLogger().setLevel(original_level)
        
        if success:
            logger.info(f"[{current_time.strftime('%H:%M')}] 일봉 수집 완료")
        else:
            logger.error(f"[{current_time.strftime('%H:%M')}] 일봉 수집 실패")
    except Exception as e:
        logging.getLogger().setLevel(original_level)
        logger.error(f"[{current_time.strftime('%H:%M')}] 오류: {str(e)[:50]}...")


def main():
    """스케줄러 실행"""
    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    scheduler = BlockingScheduler()
    
    # 1분봉 수집
    scheduler.add_job(
        minute_job,
        CronTrigger(
            day_of_week='mon-fri',
            hour=f"{settings.MINUTE_JOB_HOUR_START}-{settings.MINUTE_JOB_HOUR_END}",
            minute='*',
            second=0
        ),
        id='minute_collection',
        max_instances=1
    )
    
    # 일봉 수집
    scheduler.add_job(
        daily_job,
        CronTrigger(
            day_of_week='mon-fri',
            hour=settings.DAILY_JOB_HOUR,
            minute=0,
            second=0
        ),
        id='daily_collection',
        max_instances=1
    )
    
    # 현재 시장 상태 표시
    current_time = datetime.now()
    status = get_market_status(current_time)
    
    if "휴장일" in status:
        logger.info(f"현재는 {status}입니다")
    elif "장 시작 전" in status:
        logger.info("현재는 장 시작 전 시간입니다")
    elif "장 마감" in status:
        logger.info("현재는 장 마감 시간입니다")
    elif "장중" in status:
        logger.info("현재는 장중입니다")
    else:
        logger.info(f"현재 시장 상태: {status}")
    
    logger.info(f"스케줄러 시작 - 1분봉({settings.MINUTE_JOB_HOUR_START}:00-{settings.MINUTE_JOB_HOUR_END}:30), 일봉({settings.DAILY_JOB_HOUR}:00)")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("스케줄러 종료")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
