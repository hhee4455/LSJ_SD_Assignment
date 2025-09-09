from pydantic import Field, BaseSettings

class Settings(BaseSettings):
    # 한국투자증권 OpenAPI 설정
    KIS_APP_KEY: str = Field(..., env="KIS_APP_KEY")
    KIS_APP_SECRET: str = Field(..., env="KIS_APP_SECRET")
    KIS_BASE_URL: str = Field(default="https://openapi.koreainvestment.com:9443")
    
    # AWS DynamoDB 설정
    AWS_REGION: str = Field(default="ap-northeast-2")
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    DYNAMODB_TABLE_NAME: str = Field(default="samsung_stock_data")
    
    # 데이터 수집 설정
    STOCK_CODE: str = Field(default="005930")
    RETRY_COUNT: int = Field(default=3)
    RETRY_DELAY: int = Field(default=1)
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE_PATH: str = Field(default="logs/pipeline.log")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()