from jina.logging import JinaLogger
from fastapi import status, APIRouter

from config import openapitags_config, server_config


logger = JinaLogger(context='👻 JINAD')
common_router = APIRouter()

@common_router.on_event('startup')
async def startup():
    logger.success(f'Uvicorn + FastAPI running on {server_config.HOST}:{server_config.PORT}')
    logger.success('Welcome to Jina daemon - the remote manager for jina!')


@common_router.get(
    path='/alive',
    summary='Get status of jinad',
    status_code=status.HTTP_200_OK
)
async def _status():
    """
    Used to check if the api is running (returns 200)
    """
    return {
        'status_code': status.HTTP_200_OK
    }
