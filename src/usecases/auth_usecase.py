from datetime import datetime, UTC
from jose.exceptions import ExpiredSignatureError, JWTError

from src.config import SecurityConfig
from src.api.schemas.auth_schemas import TokenSchema
from src.usecases.interfaces.db_interfaces.db_user_interface import DBUserInterface
from src.usecases.interfaces.db_interfaces.db_refresh_token_interface import DBRefreshTokenInterface
from src.usecases.errors import AuthenticationError, NotFoundDatabaseError, UserAlreadyExistsError
from src.usecases.schemas.auth_schemas import TokenData
from src.utils.security import verify_token_and_get_data, create_access_token, create_refresh_token, verify_password, \
    get_password_hash
from src.usecases.schemas.user_schemas import UserSchema, UserCreateSchema, UserRole


class AuthUseCase:

    def __init__(self, user_repo: DBUserInterface, refresh_token_repo: DBRefreshTokenInterface):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def register_new_user(self, username: str, password: str, role: UserRole) -> UserSchema:
        try:
            await self.user_repo.get_user_by_username(username)
            raise UserAlreadyExistsError(f"User with username '{username}' already exists.")
        except NotFoundDatabaseError:
            pass

        hashed_password = get_password_hash(password)

        user_data = UserCreateSchema(username=username, password=hashed_password, role=role)
        new_user = await self.user_repo.create_user(user_data)

        return new_user

    async def login_for_access_and_refresh_token(self, username: str, password: str) -> TokenSchema:
        try:
            user = await self.user_repo.get_user_by_username(username)
        except Exception:
            raise AuthenticationError("Incorrect username or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect username or password")

        access_token = create_access_token(data={"sub": user.username, "role": user.role.value, "user_id": user.id})

        refresh_token_payload = {"sub": user.username, "user_id": user.id}
        refresh_token_str = create_refresh_token(data=refresh_token_payload)

        expires_at = datetime.now(UTC) + SecurityConfig().refresh_token_expires
        await self.refresh_token_repo.create_or_update_token(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at
        )

        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer"
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenSchema:
        try:
            token_data: TokenData = verify_token_and_get_data(refresh_token)
        except ExpiredSignatureError:
            raise AuthenticationError("Refresh token has expired.")
        except JWTError:
            raise AuthenticationError("Invalid refresh token.")

        user = await self.user_repo.get_user_by_username(token_data.username)
        if not user:
            raise AuthenticationError("User not found.")

        db_token = await self.refresh_token_repo.get_token_by_user_id(user.id)
        if not db_token or db_token.token != refresh_token:
            raise AuthenticationError("Invalid refresh token.")

        new_access_token = create_access_token(data={"sub": user.username, "role": user.role.value, "user_id": user.id})

        return TokenSchema(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
