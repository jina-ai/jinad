import time
import uuid
import asyncio
from typing import Dict
from jina.peapods.pod import MutablePod
from jina.logging import JinaLogger
from fastapi import status, APIRouter, Body
from fastapi.responses import StreamingResponse

from helper import dict_to_namespace
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
    summary='Create a MutablePod',
    tags=[TAG]
)
async def _create(
    pod_arguments: Dict
):
    """
    Used to create a MutablePod on localhost. 
    This is usually a remote pod which gets triggered by a Flow context
    
    > Shouldn't be created with manual trigger

    Args: pod_arguments (Dict)
        
        {
            'head': PodModel,
            'tail': PodModel,
            'peas': [PodModel]
        }
        
        
    """
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


def streamer(generator):
    try:
        for i in generator:
            yield i
            time.sleep(.001)

    except GeneratorExit:
        logger.info("Exiting from Pod log_iterator")


@router.get(
    path='/log',
    summary='Stream log using log_iterator',
    tags=[TAG]
)
def _log(
    pod_id: uuid.UUID
):
    """
    Stream logs from remote pod using log_iterator (This will be changed!)
    """
    with pod_store._session():
        try:
            current_pod = pod_store._store[pod_id]
            return StreamingResponse(streamer(current_pod.log_iterator))
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
