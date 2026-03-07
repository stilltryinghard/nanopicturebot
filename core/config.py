from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str
    BOT_USERNAME: str
    OWNER_ID: int
    ADMIN_IDS: list[int]

    # Database
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # ЮКасса (опционально — при заглушке оплаты не требуется)
    YUKASSA_SHOP_ID: str = ""
    YUKASSA_SECRET_KEY: str = ""

    # Legal documents (используются в онбординге)
    PRIVACY_POLICY_URL: str = "https://example.com/privacy"
    TERMS_URL: str = "https://example.com/terms"

    # AI APIs
    WAVESPEED_API_KEY: str = ""
    MIDJOURNEY_API_KEY: str = ""

    # Стоимость генерации в токенах
    TOKENS_2K: int = 10
    TOKENS_4K: int = 20

    # Реферальная программа
    REFERRAL_BONUS_TOKENS: int = 50

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore[call-arg]
