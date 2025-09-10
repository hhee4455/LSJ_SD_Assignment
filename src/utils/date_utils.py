from datetime import datetime, date, time


def get_current_timestamp() -> str:
    """현재 타임스탬프를 문자열로 반환"""
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


def is_trading_day(target_date: date = None) -> bool:
    """거래일인지 확인 (평일만 거래)"""
    if target_date is None:
        target_date = datetime.now().date()
    
    # 주말(토요일=5, 일요일=6) 제외
    return target_date.weekday() < 5


def is_trading_time(current_time: datetime = None) -> bool:
    """거래시간인지 확인 (평일 09:00-15:30)"""
    if current_time is None:
        current_time = datetime.now()
    
    # 거래일 체크
    if not is_trading_day(current_time.date()):
        return False
    
    # 거래시간 체크 (09:00-15:30)
    market_open = time(9, 0)
    market_close = time(15, 30)
    current_time_only = current_time.time()
    
    return market_open <= current_time_only <= market_close


def get_market_status(current_time: datetime = None) -> str:
    """장 상태 반환"""
    if current_time is None:
        current_time = datetime.now()
    
    if not is_trading_day(current_time.date()):
        if current_time.weekday() == 5:
            return "휴장일 (토요일)"
        elif current_time.weekday() == 6:
            return "휴장일 (일요일)"
        else:
            return "휴장일"
    
    if is_trading_time(current_time):
        return "장중"
    else:
        hour = current_time.hour
        if hour < 9:
            return "장 시작 전"
        else:
            return "장 마감"