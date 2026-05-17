from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from enum import Enum


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class TransactionBase(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    type: TransactionType
    amount: Decimal = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None
    transaction_date: date


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    type: Optional[TransactionType] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, min_length=1, max_length=255)
    notes: Optional[str] = None
    transaction_date: Optional[date] = None


class TransactionOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    user_id: int
    account_id: int
    category_id: Optional[int]
    type: TransactionType
    amount: Decimal
    description: str
    notes: Optional[str]
    transaction_date: date
    created_at: datetime


class PaginatedTransactions(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int
    pages: int
