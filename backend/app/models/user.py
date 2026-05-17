from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.category import Category
    from app.models.transaction import Transaction


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    accounts: Mapped[List["Account"]] = relationship(
        back_populates="user", cascade="all, delete", lazy="selectin"
    )
    categories: Mapped[List["Category"]] = relationship(
        back_populates="user", cascade="all, delete", lazy="selectin"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="user", cascade="all, delete", lazy="selectin"
    )
