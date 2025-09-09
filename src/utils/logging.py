import logging
import sys
from src.config.settings import settings


def get_logger(name: str) -> logging.Logger:
    """로거 생성 및 설정"""
    logger = logging.getLogger(name)

    # 중복 핸들러 방지
    if logger.handlers:
        return logger

    # 로그 레벨 설정 
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 포맷터 설정
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger