from datetime import datetime
from typing import Union

from sqlalchemy import select, update
from src.repositories.db_repositories.db_repository import BaseRepository
from src.repositories.db.models.refresh_token import RefreshToken
from src.usecases.schemas.auth_schemas import RefreshTokenSchema
from src.usecases.interfaces.db_interfaces.db_refresh_token_interface import DBRefreshTokenInterface


class DBRefreshTokenRepository(DBRefreshTokenInterface, BaseRepository):
    async def create_or_update_token(self, user_id: int, token: str, expires_at: datetime) -> RefreshTokenSchema:
        async with self as repo:
            stmt = update(RefreshToken).where(RefreshToken.user_id == user_id).values(
                token=token,
                expires_at=expires_at
            ).returning(RefreshToken)

            result = await repo._session.execute(stmt)
            updated_token = result.scalars().first()

            if updated_token:
                return RefreshTokenSchema.model_validate(updated_token)

            new_token = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
            repo._session.add(new_token)
            await repo._session.flush()

            return RefreshTokenSchema.model_validate(new_token)

    async def get_token_by_user_id(self, user_id: int) -> Union[RefreshTokenSchema, None]:
        async with self as repo:
            query = select(RefreshToken).where(RefreshToken.user_id == user_id)
            result = await repo._session.execute(query)
            token = result.scalars().first()
            if token:
                return RefreshTokenSchema.model_validate(token)
            return None