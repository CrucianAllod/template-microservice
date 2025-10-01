import logging
import sys
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from tenacity import retry, stop_after_attempt, wait_fixed
from sqlalchemy import text

from src.container import container
from src.config import LoggingConfig, RabbitMQConfig
from src.api.routes.auth_route import router as auth_router
from src.api.routes.test_route import router as test_router
from src.repositories.db.base import session_factory
from src.usecases.interfaces.rabbit_interfaces.rabbit_out_in_interface import OutInRabbitMQRepositoryInterface

_log = logging.getLogger(__name__)

logging.basicConfig(
    level=LoggingConfig().LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
async def check_rabbitmq_connection():
    """
    Check RabbitMQ connection with retry mechanism.
    """
    try:
        _log.info("Checking RabbitMQ connection availability")
        connection = await aio_pika.connect_robust(RabbitMQConfig().URL)
        await connection.close()
        _log.info("RabbitMQ connection check successful")
    except Exception as e:
        _log.error(f"RabbitMQ connection check failed: {str(e)}")
        raise


@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
async def check_db_connection():
    """
    Check DB connection with retry mechanism.
    """
    try:
        _log.info("Checking database connection availability")
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        _log.info("Database connection check successful")
    except Exception as e:
        _log.error(f"Database connection check failed: {str(e)}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    """
    _log.info("Starting Template Service initialization")

    try:
        # Verify RabbitMQ and DB are available before proceeding
        await check_rabbitmq_connection()
        await check_db_connection()
        _log.info("All dependencies are available.")

        # Initialize RabbitMQ connection and store it in app state
        _log.info("Initializing RabbitMQ connections")
        out_in_rabbit_repo = container.resolve(OutInRabbitMQRepositoryInterface)
        await out_in_rabbit_repo.connect_and_declare()
        app.state.out_in_rabbit_repo = out_in_rabbit_repo

        _log.info("All RabbitMQ connections and queues established successfully")

        _log.info("Template Service started successfully")
        yield

    except Exception as e:
        _log.critical(f"Fatal error during application startup: {str(e)}")
        raise

    finally:
        # Cleanup procedures
        _log.info("Starting application shutdown")

        # Close RabbitMQ connection
        if hasattr(app.state, 'rabbit_repo') and app.state.rabbit_repo.connection:
            await app.state.rabbit_repo.connection.close()
            _log.info("RabbitMQ connection closed")

        _log.info("Application shutdown completed")


app = FastAPI(
    title="Template Micro Service",
    description="Шаблон микросервиса",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Create main API router with /api/v1 prefix
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(test_router)

# Register the main API router
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)