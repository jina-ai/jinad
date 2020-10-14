from fastapi import APIRouter
from api.endpoints import flow

api_router = APIRouter()
api_router.include_router(router=flow.router, tags=['flow'])
