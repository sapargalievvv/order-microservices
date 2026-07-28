from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9094"

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()
