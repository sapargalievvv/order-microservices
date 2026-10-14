from functools import lru_cache

from pydantic_settings import SettingsConfigDict, BaseSettings

ALL_METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}

PUBLIC_ROUTES: dict[str, set[str]] = {
    "auth": ALL_METHODS,
    "products": {"GET", "HEAD"},
    "orders": set(),
    "users": set(),
}

BLOCKED_PREFIXES = {"products/internal"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    USER_SERVICE_URL: str
    ORDER_SERVICE_URL: str
    PRODUCTS_SERVICE_URL: str
    JWT_SECRET: str

    @property
    def service_map(self) -> dict[str, str]:
        return {
            "auth": self.USER_SERVICE_URL,
            "users": self.USER_SERVICE_URL,
            "orders": self.ORDER_SERVICE_URL,
            "products": self.PRODUCTS_SERVICE_URL,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
