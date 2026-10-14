from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Order Service"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Config
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_ORDERS_DB_PORT: int = 5433
    ORDERS_DB_NAME: str = "orders_db"

    # Redis Config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Kafka Config
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9094"

    PRODUCTS_SERVICE_URL: str = "http://localhost:8004"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """
        Формирует async DSN для подключения через asyncpg
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_ORDERS_DB_PORT}/{self.ORDERS_DB_NAME}"
        )

    @property
    def redis_url(self) -> str:
        """
        Формирует URL для подключения к Redis
        """
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()

print(settings.database_url)
