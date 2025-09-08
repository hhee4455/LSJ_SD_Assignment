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
├── .gitignore
├── app.py                # 진입점
├── config/
│   └── config.py
├── extract/
│   └── extract.py 
├── transform/
│   └── transform.py
├── load/
│   └── load.py
├── requirements.txt
└── README.md
```