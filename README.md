# 사전 평가 과제
한국투자증권 OpenAPI를 활용하여 삼성전자(005930)의 시세 데이터를 수집·정제하고, DynamoDB에 저장하는 데이터 파이프라인을 설계 및 구현합니다.

---
## 환경 세팅
- Python 3.12.4
- 의존성 패키지: `requirements.txt` 참고

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

---

## 폴더 구조
```
.
├── .env
├── .env.example
├── .gitignore
├── data
│   ├── kis_token_cache.json
│   └── kis_token.lock
├── main.py
├── README.md
├── requirements.txt
├── scheduler.py
└── src
    ├── config
    │   └── settings.py
    ├── kis
    │   ├── kis_auth.py
    │   └── kis_client.py
    ├── models
    │   ├── api_models.py
    │   └── domain_models.py
    ├── pipelines
    │   ├── extractor.py
    │   ├── loader.py
    │   └── transformer.py
    └── utils
        ├── data_utils.py
        ├── date_utils.py
        ├── logging.py
        └── retry.py
```

---

## 프로젝트 구조 설명
- `config`: 설정 관련 코드
- `kis`: 한국투자증권 OpenAPI 클라이언트 및 인증 관리
- `models`: API 및 도메인 모델 정의
- `pipelines`: ETL 파이프라인 구성 요소 (추출, 변환, 적재)
- `utils`: 유틸리티 함수 및 헬퍼 모듈

---

## 고민했던 것들

### 1. 프로젝트 구조 설계
- 모듈화를 진행하며 가독성 높은 구조가 무엇일까?
- `clients`, `models`, `pipelines`, `utils`로 역할에 따라 폴더를 나누어 관리

### 2. SMA 계산 복잡도 개선
- 최초에는 O(n^2)의 복잡도 였지만 슬라이딩 윈도우 기법을 적용하여 O(n)으로 개선

### 3. DynamoDB 테이블 설계
- 1개의 테이블에 분봉과 일봉 데이터를 모두 저장하는 방식으로 설계
- 하루에 390건의 분봉 데이터와 1건의 일봉 데이터는 한 테이블이 좋다고 판단

### 4. 토큰 관리 및 동시성 제어
- 멀티 프로세스 환경에서 토큰 충돌 방지를 위한 파일 락(fcntl) 구현
- 토큰 만료 5분 전 미리 갱신하여 API 호출 실패 방지

---

## 예외 처리

### 1. 장 마감 시간, 휴장일 예외 처리
- 스케줄러에서 거래시간과 거래일 자동 체크
- 현재 시장 상태 메시지 표시 (장중, 장 마감, 휴장일 등)

### 2. API 호출 실패 시 재시도 로직
- `@retry_with_delay` 데코레이터로 자동 재시도 (기본 3회)
- KIS API 및 DynamoDB 연결 실패 시 재시도

### 3. 데이터 검증 및 변환 오류
- 잘못된 데이터 형식 필터링
- 중복 데이터 자동 제거
- 금융 데이터 정확성을 위한 Decimal 타입 사용

### 4. DynamoDB 연결 및 저장 오류
- `ClientError` 예외 처리
- 테이블 존재 여부 확인

### 5. 토큰 관리 오류
- 토큰 만료, 오류 시 자동 갱신
- 파일 락을 통한 동시성 문제 방지