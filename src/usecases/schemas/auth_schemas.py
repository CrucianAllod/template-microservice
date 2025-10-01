from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

class RefreshTokenSchema(BaseModel):
    id: int
    user_id: int
    token: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None