from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    USERS_DB_NAME: str

    JWT_SECRET: str
    JWT_LIFETIME_SECONDS: int = 3600

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.USERS_DB_NAME}"
        )

    class Config:
        env_file = "../.env"
        extra = "ignore"

settings = Settings()