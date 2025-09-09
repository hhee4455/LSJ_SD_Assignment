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
├── main.py
├── README.md
├── requirements.txt
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

## 프로젝트 구조 설명(임시)
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
