from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./simhastha360.db"
    secret_key: str = "change-me-to-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    admin_bootstrap_phone: str = "9999999999"
    admin_bootstrap_password: str = "admin123"

    class Config:
        env_file = ".env"


settings = Settings()
