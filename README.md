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

- `main.py`: 전체 파이프라인 실행 스크립트
- `scheduler.py`: 스케줄러 설정 및 실행

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
- 토큰 충돌 방지를 위한 파일 락(fcntl) 구현
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

---

## 테이블 구성

### DynamoDB 테이블 스키마

| 컬럼명        | 타입      | 설명                        |
|--------------|----------|-----------------------------|
| PK           | 문자열   | 파티션 키 (종목+타입)        |
| SK           | 문자열   | 정렬 키 (분봉: timestamp, 일봉: date) |
| stock_code   | 문자열   | 종목 코드                   |
| open_price   | 숫자(Decimal) | 시가                    |
| high_price   | 숫자(Decimal) | 고가                    |
| low_price    | 숫자(Decimal) | 저가                    |
| close_price  | 숫자(Decimal) | 종가                    |
| volume       | 숫자     | 거래량                      |
| sma_5        | 숫자(Decimal) | 5분 이동평균(분봉만)      |
| sma_30       | 숫자(Decimal) | 30분 이동평균(분봉만)     |
| date         | 문자열   | 일자(YYYY-MM-DD, 일봉만)    |
| timestamp    | 문자열   | 시각(YYYY-MM-DD HH:MM:SS, 분봉만) |
| created_at   | 문자열   | 데이터 생성 시각             |

### 키 구조
- **PK**: `STOCK#005930#MINUTE` 또는 `STOCK#005930#DAILY` 형태
- **SK**: 분봉은 timestamp, 일봉은 date 사용

---

## 실행 

``` 
# 1번만 실행
python main.py

# 스케줄러 실행
python scheduler.py
```

---

## 실행 결과

### 콘솔 출력 예시
```
2025-09-11 11:06:00 - src.pipelines.extractor - INFO - 분봉 데이터 추출 시작
2025-09-11 11:06:00 - src.kis.kis_client - INFO - 분봉 API 호출: 005930
2025-09-11 11:06:00 - src.utils.data_utils - INFO - 중복 제거: 30 -> 30건
2025-09-11 11:06:00 - src.pipelines.extractor - INFO - 분봉 30건 추출 완료
2025-09-11 11:06:00 - main - INFO - 분봉 데이터 추출: 30건
2025-09-11 11:06:00 - src.pipelines.transformer - INFO - 분봉 데이터 변환 시작
2025-09-11 11:06:00 - src.pipelines.transformer - INFO - SMA 계산 시작: 30건
2025-09-11 11:06:00 - src.pipelines.transformer - INFO - SMA 계산 완료
2025-09-11 11:06:00 - src.pipelines.transformer - INFO - 분봉 데이터 변환 완료: 30건 처리, 1건 반환 (최신 1분)
2025-09-11 11:06:00 - src.pipelines.loader - INFO - 분봉 데이터 저장 요청: 1건
2025-09-11 11:06:00 - src.utils.data_utils - INFO - 중복 제거: 1 -> 1건
2025-09-11 11:06:00 - src.pipelines.loader - INFO - 데이터 정제 완료: 1 -> 1건
2025-09-11 11:06:00 - src.utils.data_utils - INFO - DynamoDB 아이템 변환 시작: 1건
2025-09-11 11:06:00 - src.utils.data_utils - INFO - DynamoDB 아이템 변환 완료: 1건
2025-09-11 11:06:00 - src.pipelines.loader - INFO - 배치 1/1 저장 중 (1건)
2025-09-11 11:06:00 - src.pipelines.loader - INFO - 전체 배치 저장 완료: 1건
2025-09-11 11:06:00 - main - INFO - 분봉 데이터 저장: 1건 (5분SMA, 30분SMA 포함)
2025-09-11 11:06:00 - main - INFO - 분봉 파이프라인 실행 완료!
2025-09-11 11:06:00 - main - INFO - 분봉 데이터 파이프라인 종료
2025-09-11 11:06:00 - __main__ - INFO - [11:06] 1분봉 수집 완료
```

### CSV 출력 샘플 
```csv
PK,SK,close_price,high_price,low_price,open_price,volume,sma_5,sma_30,timestamp
STOCK#005930#MINUTE,2025-09-11 10:53:00,72200,72300,72200,72250,70,72290,72483.33,2025-09-11 10:53:00
STOCK#005930#MINUTE,2025-09-11 10:54:00,72250,72300,72200,72250,30750,72270,72476.67,2025-09-11 10:54:00
STOCK#005930#DAILY,2025-09-10,72600,72800,71600,71800,21566429,,,2025-09-10 09:00:00
```

실행 결과는 루트 디렉토리의 `selected.csv` 파일에서 확인할 수 있습니다.