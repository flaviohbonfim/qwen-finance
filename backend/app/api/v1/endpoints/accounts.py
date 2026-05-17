from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate, AccountOut, AccountType


router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=list[AccountOut])
async def get_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Account).where(Account.user_id == current_user.id)
    )
    accounts = result.scalars().all()
    return [AccountOut.model_validate(a) for a in accounts]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    account = Account(
        user_id=current_user.id,
        name=account_in.name,
        type=account_in.type,
        color=account_in.color,
        balance=0,
    )
    
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    return AccountOut.model_validate(account)


@router.put("/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: int,
    account_in: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account.name = account_in.name
    account.type = account_in.type
    account.color = account_in.color
    
    await db.commit()
    await db.refresh(account)
    
    return AccountOut.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    await db.delete(account)
    await db.commit()
