import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Request, HTTPException, Response, status
from app.core.config import get_settings, Settings, BLOCKED_PREFIXES, PUBLIC_ROUTES
from app.core.auth import get_user_id

logger = logging.getLogger(__name__)

HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "transfer-encoding",
        "te",
        "trailer",
        "upgrade",
        "proxy-authorization",
        "proxy-authenticate",
    }
)
EXCLUDED_RESPONSE_HEADERS = HOP_BY_HOP | {"content-encoding", "content-length"}

router = APIRouter()


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy(
    full_path: str,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    if any(full_path == p or full_path.startswith(p + "/") for p in BLOCKED_PREFIXES):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    segments = full_path.split("/", 1)
    prefix = segments[0]
    target_api = settings.service_map.get(prefix)

    if not target_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown route: /{prefix}",
        )

    url = f"{target_api.rstrip('/')}/{full_path}"

    if request.url.query:
        url = f"{url}?{request.url.query}"

    user_id: str | None = None

    if request.method not in PUBLIC_ROUTES.get(prefix, set()):
        user_id = get_user_id(request.headers.get("authorization"), settings.JWT_SECRET)

    headers = {
        k: v
        for k, v in request.headers.items()
        if k not in HOP_BY_HOP and k != "host" and not k.startswith("x-user-")
    }

    client_ip = request.client.host if request.client else "unknown"

    if user_id:
        headers["x-user-id"] = user_id

    headers["x-forwarded-for"] = client_ip
    headers["x-forwarded-proto"] = request.url.scheme
    headers["x-forwarded-host"] = request.headers.get("host", "")

    body = await request.body()
    client = request.app.state.http_client

    try:
        upstream = await client.request(
            request.method, url, headers=headers, content=body
        )
    # Частное выше общего: ConnectTimeout тоже TimeoutException, но по смыслу
    # это "сервиса нет" (502), а не "сервис не успел ответить" (504).
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        logger.warning("upstream unreachable: %s %s — %s", request.method, url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream service is unavailable",
        )
    except httpx.TimeoutException as exc:
        logger.warning("upstream timeout: %s %s — %s", request.method, url, exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream service timed out",
        )
    except httpx.RequestError as exc:
        logger.warning("upstream request failed: %s %s — %s", request.method, url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream request failed",
        )

    response = Response(content=upstream.content, status_code=upstream.status_code)

    # multi_items вместо items: Set-Cookie приходит по заголовку на куку,
    # в словаре повторы схлопнулись бы в один. append не затирает существующий.
    for key, value in upstream.headers.multi_items():
        if key not in EXCLUDED_RESPONSE_HEADERS:
            response.headers.append(key, value)

    return response
