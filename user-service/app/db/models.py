from app.db.base import Base
from fastapi_users.db import SQLAlchemyBaseUserTableUUID


class User(SQLAlchemyBaseUserTableUUID, Base):
    # id, email, hashed_password, is_active, is_superuser, is_verified
    # приходят из SQLAlchemyBaseUserTableUUID
    pass
