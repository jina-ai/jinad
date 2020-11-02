from fastapi import status, APIRouter

common_router = APIRouter()


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
