import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# Токены выпускает user-service (fastapi-users), проверяем их локально
# общим JWT_SECRET — ходить в user-service на каждый запрос не нужно.
JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = "fastapi-users:auth"  # дефолтная audience JWTStrategy

security = HTTPBearer()


async def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            creds.credentials,
            settings.JWT_SECRET,
            algorithms=[JWT_ALGORITHM],  # явный список: иначе возможна подмена алгоритма
            audience=JWT_AUDIENCE,  # без этого примем токен сброса пароля
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )
    return user_id
