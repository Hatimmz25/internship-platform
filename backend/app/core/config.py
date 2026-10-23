from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "InternshipRadar AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    POSTGRES_SERVER: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "internship_radar"
    DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:3000"
    PUBLIC_API_URL: str = "http://localhost:8000/api/v1"

    EMAIL_PROVIDER: str = "console"
    EMAIL_FROM: str = "alerts@internshipradar.ai"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    RESEND_API_KEY: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:5432/{self.POSTGRES_DB}"
            )
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == "change-me":
            raise RuntimeError("Set a real SECRET_KEY in production.")


settings = Settings()