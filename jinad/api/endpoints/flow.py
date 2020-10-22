import uuid
import json
from ruamel.yaml import YAML
from typing import List, Union, Optional
from fastapi import status, APIRouter, Body, Response, WebSocket

from jina import __default_host__
from jina.peapods.pod import FlowPod
from jina.clients import py_client
from jina.excepts import GRPCServerError

from config import openapitags_config
from models.pod import PodModel
from excepts import FlowYamlParseException, HTTPException
from logger import get_logger
from helper import Flow

logger = get_logger(context='flow-api')
router = APIRouter()
TAG = openapitags_config.FLOW_API_TAGS[0]['name']
# TODO: to be changed to a app level global context
# fastapi recommends using global vars, will take inspiration from flask    
flow_dict = {}

class FlowWrapper:
    def __init__(self, 
                 pods: List[PodModel] = None,
                 yaml_spec: str = None):
        # TODO: to be changed to ExitStack implementation
        if pods:
            self.f = Flow()
            self.pods = pods
            self._build_with_pods()
        
        if yaml_spec:
            yaml = YAML()
            yaml.register_class(Flow)
            try:
                self.f = yaml.load(yaml_spec)
            except Exception as e:
                logger.error(f'Got error while loading from yaml {e}')
                raise FlowYamlParseException
        
        self.start()

    def _build_with_pods(self):
        for pod in self.pods:
            self.f = self.f.add(
                name=pod.name,
                uses=pod.uses,
                host=pod.host,
                port_expose=pod.port_expose,
                timeout_ready=-1,
                parallel=1
            )
        
    def start(self):
        self.f = self.f.__enter__()
        
    def close(self):
        self.f.__exit__()


@router.on_event('startup')
async def startup():
    logger.info('Welcome to Jina daemon. You can start playing with Flows!')


@router.put(
    path='/flow',
    summary='Build & start a flow using Pods',
    tags=[TAG]
)
def _create(
    config: Union[List[PodModel], str] = Body(..., 
                                              example=json.loads(PodModel().json()))
):
    """
    Used to enter a Flow context manager
    
    Accepts 
        - A List of Pods
        Example:
        
            ```
            [   
                {       
                    "name": "pod1",
                    "uses": "_pass"
                },
                {
                    "name": "pod1",
                    "uses": "_pass",
                    "host": "10.18.3.127",
                    "port_expose": 8000
                }
            ]
            ```
            
        - Flow yaml
        Example:
            ```
            To be added
            ```
    """
    global flow_dict

    if isinstance(config, str):
        try:
            flow_wrapper = FlowWrapper(yaml_spec=config)
        except FlowYamlParseException:
            raise HTTPException(status_code=404,
                                detail=f'Invalid yaml file.')
        except Exception as e:
            logger.error(f'Got error while loading yaml file {e}')
            raise HTTPException(status_code=404,
                                detail=f'Invalid yaml file.')

    if isinstance(config, list):
        flow_wrapper = FlowWrapper(pods=config)
    
    flow_id = uuid.uuid1()
    flow_dict[flow_id] = flow_wrapper

    return {
        'status_code': status.HTTP_200_OK,
        'flow_id': flow_id,
        'host': flow_wrapper.f.host,
        'port': flow_wrapper.f.port_expose,
        'status': 'started'
    }


@router.get(
    path='/flow/{flow_id}',
    summary='Get flow from flow id',
    tags=[TAG]  
)
async def _fetch(
    flow_id: uuid.UUID, 
    yaml_only: bool = False
):
    global flow_dict
    try:
        flow_wrapper = flow_dict[flow_id]
        # TODO: Fix - This fails with the inherited class
        # yaml_spec = flow_wrapper.f.yaml_spec
        # if yaml_only:
        #     return Response(content=yaml_spec,
        #                     media_type='application/yaml')
        return {
            'status_code': status.HTTP_200_OK,
            # 'yaml': yaml_spec,
            'host': flow_wrapper.f.host,
            'port': flow_wrapper.f.port_expose
        }
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Flow ID {flow_id} not found! Please create a new Flow')


@router.get(
    path='/ping',
    summary='Check grpc connection',
    tags=[TAG]
)
def _ping(
    host: str, 
    port: int
):
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
    summary='Delete flow',
    tags=[TAG]
)
def _delete(
    flow_id: uuid.UUID
):
    global flow_dict
    try:
        flow_wrapper = flow_dict[flow_id]
        flow_wrapper.f.close()
        flow_dict.pop(flow_id)
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
    global flow_dict
    if flow_dict:
        for flow_id, flow in flow_dict.copy().items():
            logger.info(f'flow id `{flow_id}` still alive! Closing it!')
            flow.f.close()
            flow_dict.pop(flow_id)
