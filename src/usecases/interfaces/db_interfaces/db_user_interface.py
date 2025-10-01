from abc import ABC, abstractmethod

from src.usecases.schemas.user_schemas import UserCreateSchema, UserSchema


class DBUserInterface(ABC):

    @abstractmethod
    async def create_user(self, data: UserCreateSchema) -> UserSchema:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> UserSchema:
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> UserSchema:
        pass

    @abstractmethod
    async def update_user_password(self, user_id: int, new_password_hash: str) -> UserSchema:
        pass