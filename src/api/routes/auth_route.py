import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.utils.dependencies import get_auth_use_case, get_current_user
from src.usecases.auth_usecase import AuthUseCase
from src.usecases.errors import AuthenticationError, UserAlreadyExistsError
from src.api.schemas.auth_schemas import TokenSchema, RefreshTokenRequest, UserRegisterRequest
from src.usecases.schemas.auth_schemas import TokenData
from src.usecases.schemas.user_schemas import UserSchema

_log = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user_route(
        request: UserRegisterRequest,
        auth_use_case: AuthUseCase = Depends(get_auth_use_case),
        current_user: TokenData = Depends(get_current_user)
):

    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can register new users."
        )

    try:
        new_user = await auth_use_case.register_new_user(
            username=request.username,
            password=request.password,
            role=request.role
        )
        return new_user
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/login", response_model=TokenSchema)
async def login_route(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    try:
        tokens = await auth_use_case.login_for_access_and_refresh_token(
            username=form_data.username,
            password=form_data.password
        )
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenSchema)
async def refresh_token_route(
        request: RefreshTokenRequest,
        auth_use_case: AuthUseCase = Depends(get_auth_use_case)
):
    try:
        tokens = await auth_use_case.refresh_access_token(
            refresh_token=request.refresh_token
        )
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )