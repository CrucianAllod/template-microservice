import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.repositories.db.models.user import User
from src.repositories.db_repositories.db_repository import BaseRepository
from src.usecases.interfaces.db_interfaces.db_user_interface import DBUserInterface
from src.usecases.schemas.user_schemas import UserCreateSchema, UserSchema
from src.usecases.errors import NotFoundDatabaseError
from src.usecases.interfaces.cache_interface import Cache

_log = logging.getLogger(__name__)


class DBUserRepository(DBUserInterface, BaseRepository):
    ALL_USER_KEY_PREFIX = "user"
    EXPIRE_TIME = 60 * 60 * 24

    def __init__(self, session_factory: async_sessionmaker, cache: Cache) -> None:
        super().__init__(session_factory)
        self._cache = cache

    async def _get_user_by_id_from_db(self, user_id: int) -> UserSchema:
        _log.info(f"Attempting to fetch user with ID {user_id} from the database.")
        async with self as repo:
            query = select(User).where(User.id == user_id)
            result = await repo._session.execute(query)
            user = result.scalars().first()

            if not user:
                _log.warning(f"User with ID {user_id} not found in DB.")
                raise NotFoundDatabaseError(f"User with user_id {user_id} not found.")

            _log.info(f"Successfully fetched user '{user.username}' (ID: {user_id}) from DB.")
            return UserSchema.model_validate(user)

    async def _get_user_by_username_from_db(self, username: str) -> UserSchema:
        _log.info(f"Attempting to fetch user with username '{username}' from the database.")
        async with self as repo:
            query = select(User).where(User.username == username)
            result = await repo._session.execute(query)
            user = result.scalars().first()

            if not user:
                _log.warning(f"User with username '{username}' not found in DB.")
                raise NotFoundDatabaseError(f"User with username {username} not found.")

            _log.info(f"Successfully fetched user '{username}' from DB.")
            return UserSchema.model_validate(user)

    async def _invalidate_user_cache(self, user: UserSchema | User):
        id_key = f"{self.ALL_USER_KEY_PREFIX}:id:{user.id}"
        username_key = f"{self.ALL_USER_KEY_PREFIX}:username:{user.username}"
        _log.info(f"Invalidating cache for user ID: {user.id} and username: {user.username}.")
        await self._cache.delete(id_key, username_key)
        _log.debug(f"Cache keys deleted: {id_key}, {username_key}")

    async def get_user_by_id(self, user_id: int) -> UserSchema:
        id_key = f"{self.ALL_USER_KEY_PREFIX}:id:{user_id}"
        _log.debug(f"Attempting to get user by ID {user_id}. Cache key: {id_key}")

        user_schema_dict = await self._cache.get_cached_or_call(
            self._get_user_by_id_from_db,
            user_id,
            key=id_key,
            ttl=self.EXPIRE_TIME,
        )
        _log.info(f"Resolved user by ID {user_id} (from cache or DB).")
        return UserSchema.model_validate(user_schema_dict)

    async def get_user_by_username(self, username: str) -> UserSchema:
        username_key = f"{self.ALL_USER_KEY_PREFIX}:username:{username}"
        _log.debug(f"Attempting to get user by username '{username}'. Cache key: {username_key}")

        user_schema_dict = await self._cache.get_cached_or_call(
            self._get_user_by_username_from_db,
            username,
            key=username_key,
            ttl=self.EXPIRE_TIME,
        )
        _log.info(f"Resolved user by username '{username}' (from cache or DB).")
        return UserSchema.model_validate(user_schema_dict)

    async def create_user(self, data: UserCreateSchema) -> UserSchema:
        _log.info(f"Creating new user with username: {data.username}")
        async with self as repo:
            new_user = User(
                username=data.username,
                hashed_password=data.password,
                role=data.role,
            )
            repo._session.add(new_user)
            await repo._session.flush()
            user_schema = UserSchema.model_validate(new_user)
            _log.info(f"New user created successfully. ID: {new_user.id}")

            await self._invalidate_user_cache(user_schema)

            return user_schema

    async def update_user_password(self, user_id: int, new_password_hash: str) -> UserSchema:
        _log.info(f"Updating password for user ID: {user_id}")
        async with self as repo:
            query = select(User).where(User.id == user_id)

            result = await repo._session.execute(query)
            user = result.scalars().first()

            if not user:
                _log.warning(f"Cannot update password. User ID {user_id} not found.")
                raise NotFoundDatabaseError(f"User with user_id {user_id} not found.")

            user.hashed_password = new_password_hash
            _log.info(f"Password for user ID {user_id} updated and flushed to DB.")

            user_schema = UserSchema.model_validate(user)
            await self._invalidate_user_cache(user_schema)

            return user_schema