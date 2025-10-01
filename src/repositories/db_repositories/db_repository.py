from sqlalchemy import delete
from typing import Self, TypeVar
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.repositories.db.base import Base
from src.usecases.errors import NotFoundDatabaseError

# Generic type for SQLAlchemy model classes
_ModelType = TypeVar("_ModelType", bound=Base)


class BaseRepository:
    """
    Base repository class providing common database operations.

    Implements async context manager pattern and basic CRUD operations
    with proper transaction handling and error management.
    """

    def __init__(self, session_factory: async_sessionmaker) -> None:
        """
        Initialize repository with session factory.

        Args:
            session_factory: Async session factory for database operations
        """
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        """
        Enter async context manager.

        Returns:
            Self: Repository instance with active database session
        """
        self._session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit async context manager with proper transaction handling.

        Args:
            exc_type: Exception type if raised in context
            exc_val: Exception value if raised in context
            exc_tb: Exception traceback if raised in context

        Notes:
            Commits transaction on success, rolls back on exception,
            and always closes the session
        """
        try:
            await self._session.commit()
        except Exception as e:
            await self._session.rollback()
            raise e
        finally:
            await self._session.close()

    async def commit(self) -> None:
        """Explicitly commit current transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back current transaction."""
        await self._session.rollback()

    async def _delete(self, model: type[_ModelType], entity_id: int) -> None:
        """
        Delete entity by ID from specified model.

        Args:
            model: SQLAlchemy model class
            entity_id: ID of entity to delete

        Notes:
            Executes DELETE query without returning result
        """
        query = delete(model).where(model.id == entity_id)
        await self._session.execute(query)

    async def _update(self, model: type[_ModelType], data: BaseModel, entity_id: int) -> BaseModel:
        """
        Update entity with validated data using Pydantic schema.

        Args:
            model: SQLAlchemy model class
            data: Pydantic schema with update data
            entity_id: ID of entity to update

        Returns:
            BaseModel: Updated entity as Pydantic model

        Raises:
            NotFoundDatabaseError: If entity with specified ID doesn't exist
            ValueError: If nested schemas are detected in update data

        Notes:
            Only updates fields explicitly set in Pydantic model (exclude_unset=True)
            Prevents nested schema updates which are not supported
        """
        model_instance = await self._session.get(model, entity_id)
        if model_instance is None:
            raise NotFoundDatabaseError(f"Item with id {entity_id} not found")

        # Update only explicitly set fields from Pydantic model
        for key, value in data.model_dump(exclude_unset=True).items():
            if isinstance(value, BaseModel):
                raise ValueError(
                    f"Schema should not contain nested schemas! Key {key} contains {value.__class__.__name__} schema.",
                )

            setattr(model_instance, key, value)

        await self._session.flush()

        return model_instance