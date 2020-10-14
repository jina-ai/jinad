import uuid
from ruamel.yaml import YAML
from jina.flow import Flow
from jina.clients import py_client
from jina.excepts import GRPCServerError
from typing import List, Union, Optional
from fastapi import APIRouter, Body, Response

from models.pod import PodBase, PodBaseExample, PodContainer
from excepts import FlowYamlParseException, HTTPException
from logger import get_logger

logger = get_logger(context='flow-api')
router = APIRouter()
flow_dict = {}


class FlowWrapper:
    def __init__(self, 
                 pods: List[PodBase] = None,
                 yaml_spec=None):
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
                uses=pod.uses
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
    summary='Build & start a flow using Pods'
)
def flow_init(
    config: Union[List[PodBase], str] = Body(..., example=PodBaseExample)
):
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
        'status_code': 200,
        'flow_id': flow_id,
        'host': flow_wrapper.f.host,
        'port': flow_wrapper.f.port_expose,
        'status': 'started'
    }


@router.get(
    path='/flow/{flow_id}',
    summary='Get flow from flow id'    
)
async def fetch_flow(
    flow_id: uuid.UUID, 
    yaml_only: bool = False
):
    global flow_dict
    try:
        flow_wrapper = flow_dict[flow_id]
        yaml_spec = flow_wrapper.f.yaml_spec
        if yaml_only:
            return Response(content=yaml_spec,
                            media_type='application/yaml')
        return {
            'status_code': 200,
            'yaml': yaml_spec,
            'host': flow_wrapper.f.host,
            'port': flow_wrapper.f.port_expose
        }
    except KeyError:
        raise HTTPException(status_code=404,
                            detail=f'Flow ID {flow_id} not found! Please create a new Flow')


@router.get(
    path='/ping',
    summary='Check grpc connection'
)
def ping_checker(
    host: str, 
    port: int
):
    try:
        py_client(port_expose=port, 
                  host=host)
        return {
            'status_code': 200,
            'detail': 'connected'
        }
    except GRPCServerError:
        raise HTTPException(status_code=404,
                            detail=f'Cannot connect to GRPC Server on {host}:{port}')


@router.delete(
    path='/flow',
    summary='Delete flow'
)
def destroy_flow(
    flow_id: uuid.UUID
):
    global flow_dict
    try:
        flow_wrapper = flow_dict[flow_id]
        flow_wrapper.f.close()
        flow_dict.pop(flow_id)
        return {
            'status_code': 200
        }
    except KeyError:
        raise HTTPException(status_code=404,
                            detail=f'Flow ID {flow_id} not found! Please create a new Flow')


@router.on_event('shutdown')
def shutdown():
    global flow_dict
    if flow_dict:
        for _id, flow in flow_dict:
            logger.info(f'flow id {_id} still alive! Closing it!')
            flow.f.close()
            flow_dict.pop(_id)
