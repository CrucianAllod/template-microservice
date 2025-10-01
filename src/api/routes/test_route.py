from fastapi import APIRouter, Depends, status

from src.api.utils.dependencies import get_current_user, get_producer_use_case
from src.api.schemas.test_schemas import TestMessage
from src.usecases.producer_usecase import ProducerUseCase
from src.usecases.schemas.auth_schemas import TokenData

router = APIRouter(prefix="/test", tags=["Test"])


@router.post(
    "/push_task",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Отправка тестового сообщения в RabbitMQ"
)
async def push_test_task(
        data: TestMessage,
        producer_usecase: ProducerUseCase = Depends(get_producer_use_case),
        current_user: TokenData = Depends(get_current_user)
):
    message_data = data.model_dump()
    result = await producer_usecase.push_test_message(message_data)
    return result