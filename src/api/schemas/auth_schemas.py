from pydantic import BaseModel
from src.usecases.schemas.user_schemas import UserRole

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    role: UserRole