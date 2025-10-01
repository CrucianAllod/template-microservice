from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship

from src.repositories.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    role = Column(Enum('admin', 'user', name='user_role_enum'), nullable=False, index=True)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"