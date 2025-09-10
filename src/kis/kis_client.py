import requests
from typing import Dict, Any

from src.config.settings import settings
from src.utils.logging import get_logger
from src.utils.retry import retry_with_delay
from src.kis.kis_auth import KISAuthManager

logger = get_logger(__name__)


class KISAPIClient:
    """KIS 시세 관련 REST 호출 래퍼"""

    def __init__(self, auth_manager: KISAuthManager):
        self.auth_manager = auth_manager
        self.base_url = settings.KIS_BASE_URL

    @retry_with_delay((requests.RequestException,))
    def _make_request(self, endpoint: str, headers: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
        """API 요청 실행 - 토큰 오류 시 재발급"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            rt_cd = result.get("rt_cd", "")
            
            # 토큰 관련 오류 체크
            if rt_cd in ["EGW00123", "EGW00124"]:  # 토큰 만료/무효
                logger.warning("토큰 오류 감지, 토큰 무효화 후 재시도")
                self.auth_manager.invalidate_token()
                raise requests.RequestException("Token expired, retrying...")
            
            # rt_cd가 "0"이거나 빈 문자열이면 성공
            if rt_cd != "0" and rt_cd != "":
                error_msg = result.get('msg1') or result.get('msg_cd') or '알 수 없는 API 오류'
                raise ValueError(f"API 오류 [{rt_cd}]: {error_msg}")
                
            return result
            
        except requests.RequestException as e:
            logger.warning(f"API 요청 실패: {e}")
            raise

    def call_minute_api(self, stock_code: str) -> Dict[str, Any]:
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
        headers = self.auth_manager.get_auth_headers(tr_id="FHKST03010200")
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_HOUR_1": "",
            "FID_PW_DATA_INCU_YN": "Y",
            "FID_ETC_CLS_CODE": "",
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
            "fid_period_div_code": "D",
            "fid_org_adj_prc": "0",
        }
        logger.info(f"일봉 API 호출: {stock_code}")
        return self._make_request(endpoint, headers, params)
