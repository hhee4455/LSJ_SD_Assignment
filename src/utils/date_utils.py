from datetime import datetime


def get_current_timestamp() -> str:
    """현재 타임스탬프를 문자열로 반환 (한국시간 기준)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_kis_date_to_iso(date_str: str) -> str:
    """KIS 날짜 형식(YYYYMMDD)을 ISO 형식(YYYY-MM-DD)으로 변환"""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"


def format_kis_time_to_iso(time_str: str) -> str:
    """KIS 시간 형식(HHMMSS)을 ISO 형식(HH:MM:SS)으로 변환"""
    return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"


def format_kis_datetime_to_iso(date_str: str, time_str: str) -> str:
    """KIS 날짜+시간을 ISO datetime 형식으로 변환"""
    date = format_kis_date_to_iso(date_str)
    time = format_kis_time_to_iso(time_str)
    return f"{date} {time}"


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