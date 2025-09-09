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

## 폴더 구조
```
.
├── .env
├── .env.example
├── .gitignore
├── app.py
├── config
│   └── settings.py
├── README.md
├── requirements.txt
├── src
│   ├── extract
│   │   └── extract.py
│   ├── load
│   │   └── load.py
│   ├── models
│   │   └── models.py
│   └── transform
│       └── transform.py
└── utils
    ├── datetime_utils.py
    ├── logging.py
    └── retry.py
```

## 고민했던 것들

### 1. 프로젝트 구조 설계
- 모듈화를 진행하며 가독성 높은 구조가 무엇일까?
- `extract`, `transform`, `load` 폴더로 나누어 각 단계별로 역할을 분리하는게 가장 가독성이 높다고 판단