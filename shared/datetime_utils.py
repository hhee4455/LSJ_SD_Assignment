from datetime import datetime


def get_current_timestamp() -> str:
    """현재 타임스탬프를 문자열로 반환 (한국시간 기준)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_market_open() -> bool:
    """현재 시장이 열려있는지 확인 (평일 09:00-15:30)"""
    now = datetime.now()
    
    # 주말 체크
    if now.weekday() >= 5:
        return False
    
    # 시장 시간 체크 (09:00-15:30)
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close