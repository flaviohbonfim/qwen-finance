from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.category import Category, CategoryType
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
async def get_categories(
    type: CategoryType | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Category).where(Category.user_id == current_user.id)
    
    if type:
        query = query.where(Category.type == type)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    return [CategoryOut.model_validate(c) for c in categories]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    category = Category(
        user_id=current_user.id,
        name=category_in.name,
        type=category_in.type,
        icon=category_in.icon,
        color=category_in.color,
    )
    
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return CategoryOut.model_validate(category)


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category.name = category_in.name
    category.type = category_in.type
    category.icon = category_in.icon
    category.color = category_in.color
    
    await db.commit()
    await db.refresh(category)
    
    return CategoryOut.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    await db.delete(category)
    await db.commit()
