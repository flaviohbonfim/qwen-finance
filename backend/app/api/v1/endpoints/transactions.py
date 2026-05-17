from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionOut,
    PaginatedTransactions,
)


router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _update_account_balance(
    account: Account,
    transaction_type: TransactionType,
    amount: Decimal,
    is_addition: bool
):
    """Atualiza o saldo da conta baseado no tipo e valor da transação."""
    if transaction_type == TransactionType.income:
        if is_addition:
            account.balance += float(amount)
        else:
            account.balance -= float(amount)
    else:  # expense
        if is_addition:
            account.balance -= float(amount)
        else:
            account.balance += float(amount)


@router.get("", response_model=PaginatedTransactions)
async def get_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    type: Optional[TransactionType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if type:
        query = query.where(Transaction.type == type)
    if date_from:
        query = query.where(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.where(Transaction.transaction_date <= date_to)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return PaginatedTransactions(
        items=[TransactionOut.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify account exists and belongs to user
    account_result = await db.execute(
        select(Account).where(
            Account.id == transaction_in.account_id,
            Account.user_id == current_user.id
        )
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Create transaction
    transaction = Transaction(
        user_id=current_user.id,
        account_id=transaction_in.account_id,
        category_id=transaction_in.category_id,
        type=transaction_in.type,
        amount=float(transaction_in.amount),
        description=transaction_in.description,
        notes=transaction_in.notes,
        transaction_date=transaction_in.transaction_date,
    )
    
    db.add(transaction)
    
    # Update account balance
    _update_account_balance(account, transaction_in.type, transaction_in.amount, True)
    
    await db.commit()
    await db.refresh(transaction)
    
    return TransactionOut.model_validate(transaction)


@router.put("/{transaction_id}", response_model=TransactionOut)
async def update_transaction(
    transaction_id: int,
    transaction_in: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get existing transaction
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Get old account for balance reversal
    old_account_result = await db.execute(
        select(Account).where(Account.id == transaction.account_id)
    )
    old_account = old_account_result.scalar_one_or_none()
    
    # Revert old transaction effect on balance
    if old_account:
        _update_account_balance(old_account, transaction.type, Decimal(str(transaction.amount)), False)
    
    # Update fields
    if transaction_in.account_id is not None:
        # Verify new account exists
        new_account_result = await db.execute(
            select(Account).where(
                Account.id == transaction_in.account_id,
                Account.user_id == current_user.id
            )
        )
        new_account = new_account_result.scalar_one_or_none()
        if not new_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        transaction.account_id = transaction_in.account_id
    
    if transaction_in.type is not None:
        transaction.type = transaction_in.type
    
    if transaction_in.amount is not None:
        transaction.amount = float(transaction_in.amount)
    
    if transaction_in.description is not None:
        transaction.description = transaction_in.description
    
    if transaction_in.notes is not None:
        transaction.notes = transaction_in.notes
    
    if transaction_in.transaction_date is not None:
        transaction.transaction_date = transaction_in.transaction_date
    
    if transaction_in.category_id is not None:
        transaction.category_id = transaction_in.category_id
    
    # Apply new transaction effect on balance
    account_result = await db.execute(
        select(Account).where(Account.id == transaction.account_id)
    )
    account = account_result.scalar_one_or_none()
    if account:
        _update_account_balance(
            account,
            transaction.type,
            Decimal(str(transaction.amount)),
            True
        )
    
    await db.commit()
    await db.refresh(transaction)
    
    return TransactionOut.model_validate(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Get account and revert balance
    account_result = await db.execute(
        select(Account).where(Account.id == transaction.account_id)
    )
    account = account_result.scalar_one_or_none()
    
    if account:
        _update_account_balance(
            account,
            transaction.type,
            Decimal(str(transaction.amount)),
            False
        )
    
    await db.delete(transaction)
    await db.commit()
