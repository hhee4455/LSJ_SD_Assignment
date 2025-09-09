import requests
from datetime import datetime, timedelta
from typing import Optional, Dict

from config.settings import settings
from utils.logging import get_logger
from utils.retry import retry_with_delay

logger = get_logger(__name__)


class KISAuthManager:
    """한국투자증권(KIS) OpenAPI 인증 토큰 관리"""

    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    @retry_with_delay((requests.RequestException,))
    def _request_token(self) -> Dict:
        """토큰 발급 API 호출"""
        url = f"{settings.KIS_BASE_URL}/oauth2/token"
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": settings.KIS_APP_KEY,
            "appsecret": settings.KIS_APP_SECRET,
        }

        logger.info("KIS 토큰 발급 요청")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get("rt_cd") != "0":
            raise ValueError(f"토큰 발급 실패: {result.get('msg1')}")

        logger.info("KIS 토큰 발급 성공")
        return result

    def is_token_valid(self) -> bool:
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.now() < self.token_expires_at

    def get_access_token(self) -> str:
        if self.is_token_valid():
            return self.access_token  # type: ignore

        result = self._request_token()
        self.access_token = result.get("access_token")
        # 공식 만료 24h, 안전 버퍼 23h
        self.token_expires_at = datetime.now() + timedelta(hours=23)
        return self.access_token  # type: ignore

    def get_auth_headers(self, tr_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "appkey": settings.KIS_APP_KEY,
            "appsecret": settings.KIS_APP_SECRET,
            "Content-Type": "application/json; charset=utf-8",
        }
        if tr_id:
            headers["tr_id"] = tr_id
        return headers
