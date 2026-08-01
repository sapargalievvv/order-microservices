from collections.abc import AsyncGenerator

from app.core.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


# Базовый класс для всех моделей SQLAlchemy
class Base(DeclarativeBase):
    pass


print(settings.database_url)
# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Логирование SQL-запросов (полезно при разработке)
    future=True,
)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Dependency Generator для FastAPI эндпоинтов
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
