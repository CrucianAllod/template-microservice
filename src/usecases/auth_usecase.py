import logging
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

_log = logging.getLogger(__name__)


class AuthUseCase:

    def __init__(self, user_repo: DBUserInterface, refresh_token_repo: DBRefreshTokenInterface):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        _log.info("AuthUseCase initialized with user and refresh token repositories.")

    async def register_new_user(self, username: str, password: str, role: UserRole) -> UserSchema:
        _log.info(f"Attempting to register new user: '{username}' with role: {role.value}.")
        try:
            await self.user_repo.get_user_by_username(username)
            _log.warning(f"Registration failed: User '{username}' already exists.")
            raise UserAlreadyExistsError(f"User with username '{username}' already exists.")
        except NotFoundDatabaseError:
            _log.debug(f"Username '{username}' is available. Proceeding with registration.")
            pass

        hashed_password = get_password_hash(password)
        _log.debug("Password successfully hashed.")

        user_data = UserCreateSchema(username=username, password=hashed_password, role=role)
        new_user = await self.user_repo.create_user(user_data)

        _log.info(f"User '{username}' registered successfully with ID: {new_user.id}.")
        return new_user

    async def login_for_access_and_refresh_token(self, username: str, password: str) -> TokenSchema:
        _log.info(f"Attempting login for user: '{username}'.")
        try:
            user = await self.user_repo.get_user_by_username(username)
            _log.debug(f"User '{username}' found in the database (ID: {user.id}).")
        except NotFoundDatabaseError:
            _log.warning(f"Login failed: Username '{username}' not found.")
            raise AuthenticationError("Incorrect username")
        except Exception as e:
            _log.error(f"Error fetching user '{username}' during login: {e}")
            raise AuthenticationError("Incorrect username")

        if not verify_password(password, user.hashed_password):
            _log.warning(f"Login failed for user '{username}': Incorrect password.")
            raise AuthenticationError("Incorrect password")

        _log.info(f"User '{username}' authenticated successfully. Creating tokens.")

        access_token = create_access_token(data={"sub": user.username, "role": user.role.value, "user_id": user.id})
        _log.debug("Access token created.")

        refresh_token_payload = {"sub": user.username, "user_id": user.id}
        refresh_token_str = create_refresh_token(data=refresh_token_payload)

        expires_at = datetime.now(UTC) + SecurityConfig().refresh_token_expires
        await self.refresh_token_repo.create_or_update_token(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at
        )
        _log.info(f"New refresh token saved/updated for user ID {user.id}. Expires at: {expires_at.isoformat()}.")

        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer"
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenSchema:
        _log.info("Attempting to refresh access token.")

        try:
            token_data: TokenData = verify_token_and_get_data(refresh_token)
            _log.debug(f"Refresh token validated. User: '{token_data.username}', ID: {token_data.user_id}.")
        except ExpiredSignatureError:
            _log.warning("Refresh token failed validation: Expired signature.")
            raise AuthenticationError("Refresh token has expired.")
        except JWTError:
            _log.warning("Refresh token failed validation: Invalid signature/structure.")
            raise AuthenticationError("Invalid refresh token.")

        try:
            user = await self.user_repo.get_user_by_id(token_data.user_id)
        except NotFoundDatabaseError:
            _log.warning(f"Refresh failed: User with ID {token_data.user_id} (from token) not found in DB.")
            raise AuthenticationError("User not found.")

        db_token = await self.refresh_token_repo.get_token_by_user_id(user.id)

        if not db_token:
            _log.warning(f"Refresh failed for user ID {user.id}: No corresponding token found in DB.")
            raise AuthenticationError("Invalid refresh token.")

        if db_token.token != refresh_token:
            _log.warning(f"Refresh failed for user ID {user.id}: Token mismatch (potential token reuse/theft).")
            raise AuthenticationError("Invalid refresh token.")

        _log.info(f"Refresh token successfully validated against database for user ID: {user.id}.")

        new_access_token = create_access_token(data={"sub": user.username, "role": user.role.value, "user_id": user.id})
        _log.info(f"New access token created for user ID {user.id}.")

        return TokenSchema(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )