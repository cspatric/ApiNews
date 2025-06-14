from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "News API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
