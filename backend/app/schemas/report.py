from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional


class MonthlySummary(BaseModel):
    month: int
    year: int
    income: Decimal
    expense: Decimal
    balance: Decimal


class CategorySummary(BaseModel):
    category_id: Optional[int]
    category_name: str
    category_color: str
    total: Decimal


class DashboardSummary(BaseModel):
    total_balance: Decimal
    month_income: Decimal
    month_expense: Decimal
    month_balance: Decimal
    last_6_months: list[MonthlySummary]
    expense_by_category: list[CategorySummary]


class YearlyReport(BaseModel):
    year: int
    months: list[MonthlySummary]
