from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from decimal import Decimal


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
