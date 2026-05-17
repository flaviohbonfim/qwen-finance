from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AccountType(str, Enum):
    checking = "checking"
    savings = "savings"
    credit_card = "credit_card"
    cash = "cash"
    investment = "investment"
    other = "other"


class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: AccountType
    color: str = Field(default="#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$")


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: AccountType
    color: str = Field(default="#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$")


class AccountOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    user_id: int
    name: str
    type: AccountType
    balance: Decimal
    color: str
    created_at: datetime
