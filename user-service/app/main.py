from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from app.db.session import create_db_and_tables
from app.db.models import User
from app.core.auth import current_active_user
from app.api import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Not needed if you setup a migration system like Alembic
    # await create_db_and_tables()
    yield


app = FastAPI(
    title="User Service",
    description="Микросервис для управления пользователями",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.auth_route)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "user_service"}


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
