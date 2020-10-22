import uuid
from argparse import Namespace
from typing import Dict
from fastapi import status, APIRouter, Body, Response
from fastapi.responses import StreamingResponse
from logger import get_logger

from jina.peapods.pod import MutablePod
from jina.enums import PeaRoleType, SchedulerType, OnErrorSkip, SocketType

from models.pod import PodModel, RemotePodModel
from config import openapitags_config
from excepts import HTTPException

logger = get_logger(context='pod-context')
router = APIRouter()
pod_dict = {}
TAG = openapitags_config.POD_API_TAGS[0]['name']


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
    global pod_dict
    
    def value_to_enum(d):
        # TODO: hardcoding to be removed using cli parser
        for key, value in d.items():
            if value is not None:
                if key == 'log_config':
                    d[key] = None
                if key == 'role':
                    d[key] = PeaRoleType(value)
                if key == 'scheduling':
                    d[key] = SchedulerType(value)
                if key == 'skip_on_error':
                    d[key] = OnErrorSkip(value)
                if key in ['socket_in', 'socket_out']:
                    d[key] = SocketType(value)
        return d
    
    def dict_to_namespace(args: Dict):
        pod_args = {}
        for pea_type, pea_args in args.items():
            # this is for pea_type: head & tail when None
            if pea_args is None:
                pod_args[pea_type] = None
            
            # this is for pea_type: head & tail
            if isinstance(pea_args, dict):
                pea_args = value_to_enum(pea_args)
                pod_args[pea_type] = Namespace(**pea_args)
            
            # this is for pea_type: peas
            if isinstance(pea_args, list):
                pod_args[pea_type] = []
                for _ in pea_args:
                    _ = value_to_enum(_)
                    pod_args[pea_type].extend([Namespace(**_)])
                
                # pod_args[pea_type].extend([Namespace(**_) for _ in pea_args]) 
        return pod_args
    
    pod_arguments = dict_to_namespace(pod_arguments)

    p = MutablePod(args=pod_arguments)
    p.start()
    
    pod_id = uuid.uuid1()
    pod_dict[pod_id] = p
    
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


async def stream_logs(current_pod):
    for l in current_pod.log_iterator:
        print(l)
        yield l


@router.get(
    path='/log',
    summary='Stream log using log_iterator',
    tags=[TAG]
)
async def _log(
    pod_id: uuid.UUID
):
    """Stream logs from remote pod

    Raises:
        HTTPException: [description]

    Returns:
        [type]: [description]
    """
    global pod_dict
    try:
        current_pod = pod_dict[pod_id]
        return StreamingResponse(stream_logs(current_pod=current_pod))            
    
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

    Args:
        pod_id (uuid.UUID): [description]
    """
    global pod_dict
    try:
        current_pod = pod_dict[pod_id]
        current_pod.close()
        pod_dict.pop(pod_id)
        return {
            'status_code': status.HTTP_200_OK
        }
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Pod ID {pod_id} not found! Please create a new Flow')


@router.on_event('shutdown')
def _shutdown():
    global pod_dict
    if pod_dict:
        for pod_id, pod in pod_dict.copy().items():
            logger.info(f'pod id `{pod_id}` still alive! Closing it!')
            pod.close()
            pod_dict.pop(pod_id)
