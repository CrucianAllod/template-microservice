from punq import Container

from src.repositories.redis_repository import RedisCacheRepository
from src.repositories.rabbit_repositories.rabbit_out_in_repository import OutInRabbitMQRepository
from src.config import RabbitMQConfig, DatabaseConfig, RedisConfig
from src.repositories.db.base import session_factory
from src.repositories.db_repositories.db_refresh_token_repository import DBRefreshTokenRepository
from src.repositories.db_repositories.db_user_repository import DBUserRepository
from src.usecases.auth_usecase import AuthUseCase
from src.usecases.interfaces.db_interfaces.db_user_interface import DBUserInterface
from src.usecases.consumer_usecase import ConsumerUseCase
from src.usecases.interfaces.db_interfaces.db_refresh_token_interface import DBRefreshTokenInterface
from src.usecases.interfaces.rabbit_interfaces.rabbit_out_in_interface import OutInRabbitMQRepositoryInterface
from src.usecases.producer_usecase import ProducerUseCase
from src.usecases.interfaces.cache_interface import Cache

container = Container()

container.register(RabbitMQConfig, instance=RabbitMQConfig())
container.register(DatabaseConfig, instance=DatabaseConfig())
container.register(RedisConfig, instance=RedisConfig())

container.register(
    Cache,
    factory=lambda: RedisCacheRepository(
        prefix=RedisConfig().PREFIX,
        host=RedisConfig().HOST,
        port=RedisConfig().PORT,
        db=RedisConfig().DB,
        password=RedisConfig().PASSWORD,
    )
)

container.register(
    DBUserInterface,
    factory=lambda: DBUserRepository(
        session_factory=session_factory,
        cache=container.resolve(Cache),
    ),
)
container.register(
    DBRefreshTokenInterface,
    factory=DBRefreshTokenRepository,
    session_factory=session_factory,
)

container.register(OutInRabbitMQRepositoryInterface, OutInRabbitMQRepository)

container.register(AuthUseCase)
container.register(ConsumerUseCase)
container.register(ProducerUseCase)
