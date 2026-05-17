from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction


class AccountType(str, enum.Enum):
    checking = "checking"
    savings = "savings"
    credit_card = "credit_card"
    cash = "cash"
    investment = "investment"
    other = "other"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[AccountType] = mapped_column(Enum(AccountType))
    balance: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", lazy="selectin"
    )
