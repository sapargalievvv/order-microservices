from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import httpx
from app import proxy


@asynccontextmanager
async def lifespan(app):
    timeout = httpx.Timeout(connect=2.0, read=10.0, write=10.0, pool=2.0)
    app.state.http_client = httpx.AsyncClient(follow_redirects=False, timeout=timeout)
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="Gateway", lifespan=lifespan)

# CORS живёт только на гейтвее: браузер разговаривает лишь с ним.
# allow_credentials=False, потому что токен ходит в заголовке Authorization,
# а не в куках — иначе "*" в origins был бы запрещён спецификацией.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev; в проде — явный список доменов фронта
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(proxy.router)
