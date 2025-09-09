import requests
import json
import os
import fcntl
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path

from src.config.settings import settings
from src.utils.logging import get_logger
from src.utils.retry import retry_with_delay

logger = get_logger(__name__)


class KISAuthManager:
    """한국투자증권 OpenAPI 인증 토큰 관리 - 파일 기반 캐싱"""

    def __init__(self):
        # 토큰 캐시 파일 경로
        self.token_cache_path = Path("data/kis_token_cache.json")
        self.lock_file_path = Path("data/kis_token.lock")
        
        # 디렉토리 생성
        self.token_cache_path.parent.mkdir(exist_ok=True)
        
        # 메모리 캐시 (성능 최적화)
        self._memory_token: Optional[str] = None
        self._memory_expires_at: Optional[datetime] = None
        
        logger.debug("KIS 인증 매니저 초기화 완료")

    def _load_token_from_cache(self) -> Optional[Dict]:
        """파일에서 토큰 정보 로드"""
        try:
            if not self.token_cache_path.exists():
                return None
            
            with open(self.token_cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # 만료 시간 문자열을 datetime으로 변환
            expires_str = cache_data.get('expires_at')
            if expires_str:
                cache_data['expires_at'] = datetime.fromisoformat(expires_str)
            
            return cache_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"토큰 캐시 파일 로드 실패: {e}")
            return None
    
    def _save_token_to_cache(self, token: str, expires_at: datetime):
        """토큰 정보를 파일에 저장"""
        try:
            cache_data = {
                'access_token': token,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            # 원자적 쓰기를 위한 임시 파일 사용
            temp_path = self.token_cache_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            # 파일 이동 (원자적 연산)
            temp_path.replace(self.token_cache_path)
            
            logger.debug("토큰 캐시 파일 저장 완료")
            
        except Exception as e:
            logger.error(f"토큰 캐시 파일 저장 실패: {e}")

    def _is_token_valid(self, token_data: Dict) -> bool:
        """토큰 유효성 검사"""
        if not token_data or 'access_token' not in token_data:
            return False
        
        expires_at = token_data.get('expires_at')
        if not expires_at:
            return False
        
        # 5분 버퍼를 두고 만료 체크
        buffer_time = datetime.now() + timedelta(minutes=5)
        return expires_at > buffer_time

    @retry_with_delay((requests.RequestException,))
    def _request_new_token(self) -> Dict:
        """새 토큰 발급 API 호출"""
        url = f"{settings.KIS_BASE_URL}/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "appkey": settings.KIS_APP_KEY,
            "appsecret": settings.KIS_APP_SECRET,
        }

        logger.info("KIS 새 토큰 발급 요청")
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()

        result = response.json()
        if "access_token" not in result:
            error_msg = result.get('error_description') or '토큰 발급 실패'
            raise ValueError(f"토큰 발급 실패: {error_msg}")

        logger.info("KIS 새 토큰 발급 성공")
        return result

    def _acquire_lock_and_get_token(self) -> str:
        """락을 획득하고 토큰을 가져오거나 발급"""
        # 락 파일을 이용한 동시성 제어
        try:
            with open(self.lock_file_path, 'w') as lock_file:
                # 비블로킹 락 시도
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except IOError:
                    # 락 획득 실패 시 잠시 대기 후 캐시에서 재로드
                    logger.debug("다른 프로세스가 토큰 발급 중, 대기...")
                    import time
                    time.sleep(2)
                    cache_data = self._load_token_from_cache()
                    if cache_data and self._is_token_valid(cache_data):
                        return cache_data['access_token']
                    raise ValueError("토큰 발급 대기 후에도 유효한 토큰 없음")
                
                # 락 획득 성공 - 다시 한번 캐시 체크
                cache_data = self._load_token_from_cache()
                if cache_data and self._is_token_valid(cache_data):
                    logger.debug("락 획득 후 캐시에서 유효한 토큰 발견")
                    return cache_data['access_token']
                
                # 새 토큰 발급
                logger.info("새 토큰 발급 시작")
                result = self._request_new_token()
                
                # 토큰 정보 저장
                access_token = result["access_token"]
                expires_at = datetime.now() + timedelta(hours=23)  # 24시간 - 1시간 버퍼
                
                # 파일과 메모리에 저장
                self._save_token_to_cache(access_token, expires_at)
                self._memory_token = access_token
                self._memory_expires_at = expires_at
                
                return access_token
                
        except Exception as e:
            logger.error(f"토큰 발급 프로세스 실패: {e}")
            raise

    def get_access_token(self) -> str:
        """액세스 토큰 획득 - 캐시 우선, 필요시 발급"""
        
        # 1. 메모리 캐시 체크 (가장 빠름)
        if (self._memory_token and self._memory_expires_at and 
            self._memory_expires_at > datetime.now() + timedelta(minutes=5)):
            logger.debug("메모리 캐시에서 토큰 반환")
            return self._memory_token
        
        # 2. 파일 캐시 체크
        cache_data = self._load_token_from_cache()
        if cache_data and self._is_token_valid(cache_data):
            # 메모리 캐시 업데이트
            self._memory_token = cache_data['access_token']
            self._memory_expires_at = cache_data['expires_at']
            logger.debug("파일 캐시에서 토큰 반환")
            return cache_data['access_token']
        
        # 3. 새 토큰 발급 (락 사용)
        logger.info("유효한 토큰이 없어 새로 발급")
        return self._acquire_lock_and_get_token()

    def invalidate_token(self):
        """토큰 무효화 (에러 발생 시 사용)"""
        logger.info("토큰 무효화")
        self._memory_token = None
        self._memory_expires_at = None
        
        try:
            if self.token_cache_path.exists():
                self.token_cache_path.unlink()
        except Exception as e:
            logger.warning(f"토큰 캐시 파일 삭제 실패: {e}")

    def is_token_valid(self) -> bool:
        """현재 토큰 유효성 체크 (외부 인터페이스)"""
        try:
            token = self.get_access_token()
            return bool(token)
        except Exception:
            return False

    def get_auth_headers(self, tr_id: Optional[str] = None) -> Dict[str, str]:
        """인증 헤더 생성"""
        try:
            headers = {
                "Authorization": f"Bearer {self.get_access_token()}",
                "appkey": settings.KIS_APP_KEY,
                "appsecret": settings.KIS_APP_SECRET,
                "Content-Type": "application/json",
            }
            if tr_id:
                headers["tr_id"] = tr_id
            return headers
        except Exception as e:
            logger.error(f"인증 헤더 생성 실패: {e}")
            raise

    def cleanup_cache(self):
        """캐시 파일 정리 (필요시 사용)"""
        try:
            if self.token_cache_path.exists():
                self.token_cache_path.unlink()
                logger.info("토큰 캐시 파일 정리 완료")
            
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
                logger.debug("락 파일 정리 완료")
                
        except Exception as e:
            logger.warning(f"캐시 정리 실패: {e}")
