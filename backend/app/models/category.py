from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[CategoryType] = mapped_column(Enum(CategoryType))
    icon: Mapped[str] = mapped_column(String(50), default="tag")
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="categories")
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="category", cascade="all, delete-orphan", lazy="selectin"
    )
