from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./simhastha360.db"
    secret_key: str = "change-me-to-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    admin_bootstrap_phone: str = "9999999999"
    admin_bootstrap_password: str = "admin123"
    mappls_key: str = ""

    class Config:
        env_file = ".env"

    @model_validator(mode="before")
    @classmethod
    def _drop_blank_env_values(cls, data):
        # Some platforms (e.g. Vercel) pass an unset dashboard env var as ""
        # rather than omitting it. Pydantic would otherwise try to parse ""
        # as e.g. an int and fail - drop blanks so the field's default applies.
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v != ""}
        return data


settings = Settings()
