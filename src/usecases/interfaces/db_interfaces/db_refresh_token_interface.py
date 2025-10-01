from abc import ABC, abstractmethod
from datetime import datetime
from typing import Union

from src.usecases.schemas.auth_schemas import RefreshTokenSchema

class DBRefreshTokenInterface(ABC):

    @abstractmethod
    async def create_or_update_token(self, user_id: int, token: str, expires_at: datetime) -> RefreshTokenSchema:
        pass

    @abstractmethod
    async def get_token_by_user_id(self, user_id: int) -> Union[RefreshTokenSchema, None]:
        pass