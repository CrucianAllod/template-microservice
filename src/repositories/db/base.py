from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.config import DatabaseConfig

db_url = DatabaseConfig().database_url
engine = create_async_engine(
    db_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)
session_factory = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine
)

Base = declarative_base()