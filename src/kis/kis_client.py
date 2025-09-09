import requests
from typing import Dict, Any

from config.settings import settings
from utils.logging import get_logger
from utils.retry import retry_with_delay
from kis_auth import KISAuthManager

logger = get_logger(__name__)


class KISAPIClient:
    """KIS 시세 관련 REST 호출 래퍼"""

    def __init__(self, auth_manager: KISAuthManager):
        self.auth_manager = auth_manager
        self.base_url = settings.KIS_BASE_URL

    @retry_with_delay((requests.RequestException,))
    def _make_request(self, endpoint: str, headers: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("rt_cd") != "0":
            raise ValueError(f"API 오류: {result.get('msg1')}")
        return result

    def call_minute_api(self, stock_code: str) -> Dict[str, Any]:
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
        headers = self.auth_manager.get_auth_headers(tr_id="FHKST03010200")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
            "fid_period_div_code": "1",  # 1분봉 고정
            "fid_org_adj_prc": "0",
        }
        logger.info(f"분봉 API 호출: {stock_code}")
        return self._make_request(endpoint, headers, params)

    def call_daily_api(self, stock_code: str, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = self.auth_manager.get_auth_headers(tr_id="FHKST03010100")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": "D",  # 일봉
            "fid_org_adj_prc": "0",
        }
        logger.info(f"일봉 API 호출: {stock_code}")
        return self._make_request(endpoint, headers, params)
