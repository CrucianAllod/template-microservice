from datetime import datetime, timezone, timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict

class RabbitMQConfig(BaseSettings):
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str
    IN_TASK_QUEUE: str
    IN_TASK_EXCHANGE: str
    OUT_TASK_QUEUE: str
    OUT_TASK_EXCHANGE: str
    CONNECTION_TIMEOUT: int
    RETRY_INTERVAL: int

    model_config = SettingsConfigDict(
        env_prefix="RABBITMQ_",
        extra="ignore",
        env_file=".env")

    @property
    def URL(self) -> str:
        return f"amqp://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/"

class DatabaseConfig(BaseSettings):
    PORT: str
    HOST: str
    DB: str
    USER: str
    PASS: str
    SSLMODE: str = "require"
    SSLROOTCERT: str = "/root/.postgresql/root.crt"

    model_config = SettingsConfigDict(env_prefix="DB_PG_", extra="ignore", env_file=".env")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.DB}"

    @property
    def utcnow(self) -> datetime:
        return datetime.now(timezone.utc)

class SecurityConfig(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        extra="ignore",
        env_file=".env"
    )

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

class RedisConfig(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_USER: str = "default"
    REDIS_PASSWORD: str = ""
    REDIS_PREFIX: str = "local"

    @property
    def REDIS_LINK(self) -> str:
        redis_address = f"{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        if self.REDIS_PASSWORD:
            return f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{redis_address}"

        return f"redis://{redis_address}"

class LoggingConfig(BaseSettings):
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_prefix="LOGGING_", extra="ignore", env_file=".env")

