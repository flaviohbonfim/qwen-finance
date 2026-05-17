from fastapi import APIRouter

from app.api.v1.endpoints import auth, accounts, categories, transactions, reports


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(categories.router)
api_router.include_router(transactions.router)
api_router.include_router(reports.router)
