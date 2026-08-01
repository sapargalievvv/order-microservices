from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "products-service"
    API_V1_STR: str = "/api/v1"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5434
    PRODUCTS_DB_NAME: str = "products_db"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    JWT_SECRET: str

    @property
    def redis_url(self) -> str:
        return f"redis://{self.host}:{self.port}/0"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.PRODUCTS_DB_NAME}"
        )

    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
