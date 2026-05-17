from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_
from sqlalchemy.orm import aliased

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.transaction import Transaction, TransactionType
from app.models.category import Category
from app.models.user import User
from app.schemas.report import (
    DashboardSummary,
    MonthlySummary,
    CategorySummary,
    YearlyReport,
)


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    current_month_start = today.replace(day=1)
    
    # Total balance from all accounts
    total_balance_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.income
        )
    )
    total_income = total_balance_result.scalar() or 0
    
    total_expense_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.expense
        )
    )
    total_expense = total_expense_result.scalar() or 0
    
    total_balance = Decimal(str(total_income)) - Decimal(str(total_expense))
    
    # Month income and expense
    month_income_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.income,
            Transaction.transaction_date >= current_month_start
        )
    )
    month_income = month_income_result.scalar() or 0
    
    month_expense_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.expense,
            Transaction.transaction_date >= current_month_start
        )
    )
    month_expense = month_expense_result.scalar() or 0
    
    month_balance = Decimal(str(month_income)) - Decimal(str(month_expense))
    
    # Last 6 months summary
    last_6_months = []
    for i in range(5, -1, -1):
        ref_date = today
        for _ in range(i):
            if ref_date.month == 1:
                ref_date = ref_date.replace(year=ref_date.year - 1, month=12)
            else:
                ref_date = ref_date.replace(month=ref_date.month - 1)
        
        month_start = ref_date.replace(day=1)
        if ref_date.month == 12:
            month_end = ref_date.replace(year=ref_date.year + 1, month=1, day=1)
        else:
            month_end = ref_date.replace(month=ref_date.month + 1, day=1)
        
        income_result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.income,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < month_end
            )
        )
        income = income_result.scalar() or 0
        
        expense_result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.expense,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < month_end
            )
        )
        expense = expense_result.scalar() or 0
        
        last_6_months.append(
            MonthlySummary(
                month=ref_date.month,
                year=ref_date.year,
                income=Decimal(str(income)),
                expense=Decimal(str(expense)),
                balance=Decimal(str(income)) - Decimal(str(expense)),
            )
        )
    
    # Expense by category (current month) - CORRECT: start from Transaction
    CategoryAlias = aliased(Category)
    category_result = await db.execute(
        select(
            Transaction.category_id,
            CategoryAlias.name,
            CategoryAlias.color,
            func.sum(Transaction.amount).label("total")
        )
        .select_from(Transaction)
        .join(CategoryAlias, Transaction.category_id == CategoryAlias.id, isouter=True)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.expense,
            Transaction.transaction_date >= current_month_start
        )
        .group_by(Transaction.category_id, CategoryAlias.name, CategoryAlias.color)
        .order_by(func.sum(Transaction.amount).desc())
    )
    
    expense_by_category = [
        CategorySummary(
            category_id=row[0],
            category_name=row[1] or "Sem categoria",
            category_color=row[2] or "#9ca3af",
            total=Decimal(str(row[3])) if row[3] else Decimal("0"),
        )
        for row in category_result.fetchall()
    ]
    
    return DashboardSummary(
        total_balance=total_balance,
        month_income=Decimal(str(month_income)),
        month_expense=Decimal(str(month_expense)),
        month_balance=month_balance,
        last_6_months=last_6_months,
        expense_by_category=expense_by_category,
    )


@router.get("/monthly", response_model=YearlyReport)
async def get_monthly_report(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if year is None:
        year = datetime.now().year
    
    months = []
    for month in range(1, 13):
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)
        
        income_result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.income,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < month_end
            )
        )
        income = income_result.scalar() or 0
        
        expense_result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.expense,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date < month_end
            )
        )
        expense = expense_result.scalar() or 0
        
        months.append(
            MonthlySummary(
                month=month,
                year=year,
                income=Decimal(str(income)),
                expense=Decimal(str(expense)),
                balance=Decimal(str(income)) - Decimal(str(expense)),
            )
        )
    
    return YearlyReport(year=year, months=months)
