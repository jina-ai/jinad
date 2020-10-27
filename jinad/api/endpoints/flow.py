import os
import uuid
import json
import tempfile
from ruamel.yaml import YAML
from typing import List, Union, Optional
from jina.clients import py_client
from fastapi import status, APIRouter, Body, Response, WebSocket, File, UploadFile

from jina.logging import JinaLogger
from models.pod import PodModel
from store import flow_store
from excepts import FlowYamlParseException, FlowCreationFailed, FlowStartFailed, \
    HTTPException, GRPCServerError
from helper import Flow, create_meta_files_from_upload, delete_meta_files_from_upload
from config import openapitags_config


logger = JinaLogger(context='👻 FLOWAPI')
router = APIRouter()
TAG = openapitags_config.FLOW_API_TAGS[0]['name']


@router.on_event('startup')
async def startup():
    logger.info('Welcome to Jina daemon. You can start playing with Flows!')


@router.put(
    path='/flow/pods',
    summary='Build & start a Flow using Pods',
    tags=[TAG]
)
def _create_from_pods(
    pods: Union[List[PodModel]] = Body(..., 
                                       example=json.loads(PodModel().json()))
):
    """
    Build a Flow using a list of `PodModel`
        
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
    """
    with flow_store._session():
        try:
            flow_id, host, port_expose = flow_store._create(config=pods)
        except FlowCreationFailed:
            raise HTTPException(status_code=404,
                                detail=f'Bad pods args')
        except FlowStartFailed:
            raise HTTPException(status_code=404,
                                detail=f'Flow couldn\'t get started')
    return {
        'status_code': status.HTTP_200_OK,
        'flow_id': flow_id,
        'host': host,
        'port': port_expose,
        'status': 'started'
    }


@router.put(
    path='/flow/yaml',
    summary='Build & start a Flow using YAML',
    tags=[TAG]
)
def _create_from_yaml(
    yamlspec: UploadFile = File(...),
    uses_files: List[UploadFile] = File([]),
    pymodules_files: List[UploadFile] = File([])
):
    """ 
    Build a flow using [Flow YAML](https://docs.jina.ai/chapters/yaml/yaml.html#flow-yaml-sytanx)

    > Upload Flow yamlspec (`yamlspec`)

    > Yamls that Pods use (`uses_files`) (Optional)

    > Python modules (`pymodules_files`) that the Pods use (Optional)

    **yamlspec**:

        !Flow
        pods:
            encode1:
                uses: test-if-encode1.yml
            encode2:
                uses: test-if-encode2.yml

    **uses_files**: `test-if-encode1.yml`

        !BaseTFEncoder
        requests:
        on:
            IndexRequest:
            - !EncodeDriver
                if: doc.mime_type.startswith('text')

    **uses_files**: `test-if-encode2.yml`

        !BaseTFEncoder
        requests:
        on:
            IndexRequest:
            - !EncodeDriver
                if: doc.mime_type.startswith('image')


    """

    with flow_store._session():
        try:
            # This makes sure `uses` & `py_modules` are created locally in `cwd`
            # TODO: Handle file creation, deletion better
            # TODO: Do we need to add support for `uses_before`, `uses_after`?
            if uses_files:
                [create_meta_files_from_upload(current_use_file) for current_use_file in uses_files]

            if pymodules_files:
                [create_meta_files_from_upload(current_pymodule_file) for current_pymodule_file in pymodules_files]

            flow_id, host, port_expose = flow_store._create(config=yamlspec.file)

            if uses_files:
                [delete_meta_files_from_upload(current_use_file) for current_use_file in uses_files]

            if pymodules_files:
                [delete_meta_files_from_upload(current_pymodule_file) for current_pymodule_file in pymodules_files]

        except FlowYamlParseException:
            raise HTTPException(status_code=404,
                                detail=f'Invalid yaml file.')
        except FlowStartFailed as e:
            raise HTTPException(status_code=404,
                                detail=f'Flow couldn\'t get started:  {repr(e)}')
    
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
        with flow_store._session():
            host, port_expose, yaml_spec = flow_store._get(flow_id=flow_id)

        if yaml_only:
            return Response(content=yaml_spec,
                            media_type='application/yaml')
        
        return {
            'status_code': status.HTTP_200_OK,
            'yaml': yaml_spec,
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
