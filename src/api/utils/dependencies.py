import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.container import container
from src.usecases.auth_usecase import AuthUseCase
from src.utils.security import verify_token_and_get_data
from src.usecases.errors import AuthenticationError
from src.usecases.schemas.auth_schemas import TokenData
from src.usecases.producer_usecase import ProducerUseCase

_log = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()


def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> TokenData:
    try:
        token_data = verify_token_and_get_data(token.credentials)
        return token_data
    except AuthenticationError as e:
        _log.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_auth_use_case() -> AuthUseCase:
    return container.resolve(AuthUseCase)

def get_producer_use_case() -> ProducerUseCase:
    return container.resolve(ProducerUseCase)