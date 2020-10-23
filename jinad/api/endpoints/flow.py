import uuid
import json
from ruamel.yaml import YAML
from typing import List, Union, Optional
from jina.clients import py_client
from fastapi import status, APIRouter, Body, Response, WebSocket

from jina.logging import JinaLogger
from models.pod import PodModel
from store import flow_store
from excepts import FlowYamlParseException, FlowCreationFailed, HTTPException, GRPCServerError
from helper import Flow
from config import openapitags_config


logger = JinaLogger(context='👻 FLOWAPI')
router = APIRouter()
TAG = openapitags_config.FLOW_API_TAGS[0]['name']


@router.on_event('startup')
async def startup():
    logger.info('Welcome to Jina daemon. You can start playing with Flows!')


@router.put(
    path='/flow',
    summary='Build & start a Flow',
    tags=[TAG]
)
def _create(
    config: Union[List[PodModel], str] = Body(..., 
                                              example=json.loads(PodModel().json()))
):
    """
    Build a Flow either using list of `PodModel` or using `Flow YAML` (converted to string)

    > A List of PodModels
        
        [
            {       
                "name": "pod1",
                "uses": "_pass"
            },
            {
                "name": "pod2",
                "uses": "_pass",
                "host": "10.18.3.127",
                "port_expose": 8000
            }
        ]

    > [Flow YAML Syntax](https://docs.jina.ai/chapters/yaml/yaml.html#flow-yaml-sytanx)
            
        To be added

    """
    with flow_store._session():
        try:
            flow_id, host, port_expose = flow_store._create(config=config)
        except FlowYamlParseException:
            raise HTTPException(status_code=404,
                                detail=f'Invalid yaml file.')
        except FlowCreationFailed:
            raise HTTPException(status_code=404,
                                detail=f'Bad pods args')
        except Exception as e:
            logger.critical(e)
            raise HTTPException(status_code=404,
                                detail=f'Something went wrong')
    return {
        'status_code': status.HTTP_200_OK,
        'flow_id': flow_id,
        'host': host,
        'port': port_expose,
        'status': 'started'
    }


@router.get(
    path='/flow/{flow_id}',
    summary='Get Flow information',
    tags=[TAG]  
)
async def _fetch(
    flow_id: uuid.UUID, 
    yaml_only: bool = False
):
    """
    Get Flow information using `flow_id`. 
    
    Following details are sent:
    - Flow YAML
    - Gateway host
    - Gateway port
    """
    try:
        # TODO: Fix - This fails with the inherited class
        # yaml_spec = flow_wrapper.f.yaml_spec
        # if yaml_only:
        #     return Response(content=yaml_spec,
        #                     media_type='application/yaml')
        with flow_store._session():
            host, port_expose = flow_store._get(flow_id=flow_id)
        
        return {
            'status_code': status.HTTP_200_OK,
            # 'yaml': yaml_spec,
            'host': host,
            'port': port_expose
        }
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Flow ID {flow_id} not found! Please create a new Flow')


@router.get(
    path='/ping',
    summary='Connect to Flow gateway',
    tags=[TAG]
)
def _ping(
    host: str, 
    port: int
):
    """
    Ping to check if we can connect to gateway `host:port`
    
    Note: Make sure Flow is running

    """
    try:
        py_client(port_expose=port, 
                  host=host)
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'connected'
        }
    except GRPCServerError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Cannot connect to GRPC Server on {host}:{port}')


@router.delete(
    path='/flow',
    summary='Close Flow context',
    tags=[TAG]
)
def _delete(
    flow_id: uuid.UUID
):
    """
    Close Flow context
    """
    with flow_store._session():
        try:
            flow_store._delete(flow_id=flow_id)
            return {
                'status_code': status.HTTP_200_OK
            }
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Flow ID {flow_id} not found! Please create a new Flow')



@router.websocket(
    path='/wslogs'
)
async def _websocket_logs(websocket: WebSocket):
    # TODO: extend this to work with fluentd logs
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f'Message text: {data}')


@router.on_event('shutdown')
def _shutdown():
    with flow_store._session():
        flow_store._delete_all()
