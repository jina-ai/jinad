import uuid
import asyncio
from typing import Dict
from jina.peapods.pod import MutablePod
from fastapi import status, APIRouter, Body
from fastapi.responses import StreamingResponse

from jina.logging import JinaLogger
from models.pod import PodModel
from store import pod_store
from excepts import HTTPException
from config import openapitags_config


TAG = openapitags_config.POD_API_TAGS[0]['name']
logger = JinaLogger(context='👻 PODAPI')
router = APIRouter()


@router.on_event('startup')
async def startup():
    logger.info('Welcome to Jina daemon for remote pods')


@router.put(
    path='/pod',
    summary='Create a MutablePod locally (triggered via a Flow)',
    tags=[TAG]
)
async def _create(
    pod_arguments: Dict
):
    """Used to create a MutablePod on localhost!
    This is usually a remote pod which gets triggered by a Flow context
    Shouldn't be created with manual trigger 

    Args:
        pod_arguments (Dict): accepts Pod args
    """    
    def dict_to_namespace(args: Dict):
        from jina.parser import set_pod_parser
        parser = set_pod_parser()
        pod_args = {}
        
        for pea_type, pea_args in args.items():
            # this is for pea_type: head & tail when None
            if pea_args is None:
                pod_args[pea_type] = None
            
            # this is for pea_type: head & tail when not None
            if isinstance(pea_args, dict):
                pea_args, _ = parser.parse_known_intermixed_args(pea_args)
                pod_args[pea_type] = pea_args
            
            # this is for pea_type: peas (multiple entries)
            if isinstance(pea_args, list):
                pod_args[pea_type] = []
                for i in pea_args:
                    _parsed, _ = parser.parse_known_intermixed_args(i)
                    pod_args[pea_type].append(_parsed)

        return pod_args
    
    pod_arguments = dict_to_namespace(pod_arguments)

    with pod_store._session():
        try:
            pod_id = pod_store._create(pod_arguments=pod_arguments)
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=404,
                                detail=f'Something went wrong')
    return {
        'status_code': status.HTTP_200_OK,
        'pod_id': pod_id,
        'status': 'started'
    }

@router.get(
    path='/alive',
    summary='Get status of jinad',
    status_code=status.HTTP_200_OK,
    tags=[TAG]
)
async def _status():
    """
    Used to check if the api is running (returns 200) 
    """
    return {
        'status_code': status.HTTP_200_OK
    }


def finite_generator():
    x = 0
    while x < 100:
        yield f"{x}"
        x += 1


async def astreamer(generator):
    try:
        for i in generator:
            yield i
            await asyncio.sleep(.001)

    except asyncio.CancelledError as e:
        print('cancelled')


@router.get(
    path='/log',
    summary='Stream log using log_iterator',
    tags=[TAG]
)
async def _log(
    pod_id: uuid.UUID
):
    """Stream logs from remote pod
    """
    with pod_store._session():
        try:
            current_pod = pod_store._store[pod_id]
            return StreamingResponse(astreamer(current_pod.log_iterator))
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Pod ID {pod_id} not found! Please create a new Flow')


@router.delete(
    path='/pod',
    summary='Delete pod',
    tags=[TAG]
)
async def _delete(
    pod_id: uuid.UUID
):
    """Close Pod context
    """
    with pod_store._session():
        try:
            pod_store._delete(pod_id=pod_id)
            return {
                'status_code': status.HTTP_200_OK
            }
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Pod ID {pod_id} not found! Please create a new Pod')


@router.on_event('shutdown')
def _shutdown():
    with pod_store._session():
        pod_store._delete_all()
