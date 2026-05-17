from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class CategoryType(str, Enum):
    income = "income"
    expense = "expense"


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: CategoryType
    icon: str = Field(default="tag", max_length=50)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: CategoryType
    icon: str = Field(default="tag", max_length=50)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    user_id: int
    name: str
    type: CategoryType
    icon: str
    color: str
    created_at: datetime
