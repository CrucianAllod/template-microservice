from enum import Enum as PyEnum

from pydantic import BaseModel, ConfigDict


class UserRole(str, PyEnum):
    USER = 'user'
    ADMIN = 'admin'


class UserCreateSchema(BaseModel):
    username: str
    password: str
    role: UserRole


class UserSchema(BaseModel):
    id: int
    username: str
    hashed_password: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)