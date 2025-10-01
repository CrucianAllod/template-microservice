from sqlalchemy import select

from config import RedisConfig
from src.repositories.db.models.user import User
from src.repositories.db_repositories.db_repository import BaseRepository
from src.usecases.interfaces.db_interfaces.db_user_interface import DBUserInterface
from src.usecases.schemas.user_schemas import UserCreateSchema, UserSchema
from src.usecases.errors import NotFoundDatabaseError
from src.usecases.interfaces.cache_interface import Cache


class DBUserRepository(DBUserInterface, BaseRepository):
    ALL_USER_KEY_PREFIX = RedisConfig().REDIS_PREFIX + ":user"
    EXPIRE_TIME = 60 * 60 * 24

    def __init__(self, session_factory, cache: Cache) -> None:
        super().__init__(session_factory)
        self.cache = cache

    async def _get_user_by_id_from_db(self, user_id: int) -> UserSchema:
        async with self as repo:
            query = select(User).where(User.id == user_id)
            result = await repo._session.execute(query)
            user = result.scalars().first()

            if not user:
                raise NotFoundDatabaseError(f"User with user_id {user_id} not found.")

            return UserSchema.model_validate(user)

    async def _get_user_by_username_from_db(self, username: str) -> UserSchema:
        async with self as repo:
            query = select(User).where(User.username == username)
            result = await repo._session.execute(query)
            user = result.scalars().first()

            if not user:
                raise NotFoundDatabaseError(f"User with username {username} not found.")

            return UserSchema.model_validate(user)

    async def _invalidate_user_cache(self, user: UserSchema | User):
        id_key = f"{self.ALL_USER_KEY_PREFIX}:id:{user.id}"
        username_key = f"{self.ALL_USER_KEY_PREFIX}:username:{user.username}"
        await self.cache.delete(id_key, username_key)

    async def get_user_by_id(self, user_id: int) -> UserSchema:
        id_key = f"{self.ALL_USER_KEY_PREFIX}:id:{user_id}"
        user = await self.cache.get_cached_or_call(
            key=id_key,
            expire_time=self.EXPIRE_TIME,
        )(self._get_user_by_id_from_db)(user_id)

        return user

    async def get_user_by_username(self, username: str) -> UserSchema:
        username_key = f"{self.ALL_USER_KEY_PREFIX}:username:{username}"
        user = await self.cache.get_cached_or_call(
            key=username_key,
            expire_time=self.EXPIRE_TIME,
        )(self._get_user_by_username_from_db)(username)

        return user

    async def create_user(self, data: UserCreateSchema) -> UserSchema:
        async with self as repo:
            new_user = User(
                username=data.username,
                hashed_password=data.password,
                role=data.role,
            )
            repo._session.add(new_user)
            await repo._session.flush()
            user_schema = UserSchema.model_validate(new_user)
            await self._invalidate_user_cache(user_schema)

            return user_schema

    async def update_user_password(self, user_id: int, new_password_hash: str) -> UserSchema:
        async with self as repo:
            query = select(User).where(User.id == user_id)

            result = await repo._session.execute(query)
            user = result.scalars().first()

            if not user:
                raise NotFoundDatabaseError(f"User with user_id {user_id} not found.")

            user.hashed_password = new_password_hash
            user_schema = UserSchema.model_validate(user)
            await self._invalidate_user_cache(user_schema)

            return user_schema