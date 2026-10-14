import jwt
from fastapi import HTTPException, status

JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = "fastapi-users:auth"  # дефолтная audience JWTStrategy


def unauthorized(details: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=details,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_id(auth_header: str | None, secret: str) -> str:
    if not auth_header:
        raise unauthorized("no auth headers")

    # Пробел в схеме обязателен: иначе голый "Bearer" пройдёт проверку
    # и упадёт с IndexError на split — клиент получит 500 вместо 401.
    if not auth_header.lower().startswith("bearer "):
        raise unauthorized("not bearer")

    token = auth_header.split(" ", 1)[1].strip()

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[
                JWT_ALGORITHM
            ],  # явный список: иначе возможна подмена алгоритма
            audience=JWT_AUDIENCE,  # без этого примем токен сброса пароля
        )
    except jwt.PyJWTError:
        raise unauthorized("Invalid token")

    user_id = payload.get("sub")

    if not user_id:
        raise unauthorized("Invalid token payload")

    return user_id
