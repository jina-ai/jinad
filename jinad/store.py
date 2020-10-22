import uuid
from typing import List, Union
from contextlib import contextmanager
from ruamel.yaml import YAML
from jina.flow import Flow

from logger import get_logger
from models.pod import PodModel
from excepts import FlowYamlParseException, FlowCreationFailed


class InMemoryFlowStore:
    
    _store = {}
    # TODO: Implement fastapi based oauth/bearer security here
    credentials = 'foo:bar'
    _session_token = None
    logger = get_logger(context='flow-api')
    
    @contextmanager
    def _session(self):
        if self._session_token:
            yield
            return

        self._session_token = self._login(self.credentials)
        try:
            yield
        finally:
            self._logout(self._session_token)
    
    # TODO: implement login-logout here to manage session token
    def _login(self, creds):
        token = hash(creds)
        self.logger.info(f'LOGIN: {token}')
        return token
    
    def _logout(self, token):
        self.logger.info(f'LOGOUT: {token}')
    
    def _create(self, config: Union[str, List[PodModel]] = None):
        flow_id = uuid.uuid4()

        if isinstance(config, str):
            yaml = YAML()
            try:
                yaml.register_class(Flow)
                f = yaml.load(config)
            except Exception as e:
                self.logger.error(f'Got error while loading from yaml {e}')
                raise FlowYamlParseException

        if isinstance(config, list):
            f = Flow()
            try:
                f = self._build_with_pods(flow=f, pods=config)
            except Exception as e:
                self.logger.error(f'Got error while creating flows via pods {e}')
                raise FlowCreationFailed

        self._start(flow=f)
        self._store[flow_id] = f
        self.logger.info(f'Started flow with flow_id {flow_id}')
        return flow_id, f.host, f.port_expose
    
    # TODO: change this to pod_args 
    def _build_with_pods(self, flow, pods):
        for pod in pods:
            flow = flow.add(
                name=pod.name,
                uses=pod.uses,
                host=pod.host,
                port_expose=pod.port_expose,
                timeout_ready=-1,
                parallel=1
            )
        return flow
    
    def _start(self, flow):
        flow.start()
    
    def _get(self, flow_id):
        if flow_id not in self._store:
            raise KeyError(f'{flow_id} not found')
        f = self._store[flow_id]
        return f.host, f.port_expose
        
    def _delete(self, flow_id):
        if flow_id not in self._store:
            raise KeyError(f'flow_id {flow_id} not found in store. please create one!')
        f = self._store.pop(flow_id)
        f.close()
        self.logger.info(f'Closed flow with flow_id {flow_id}')
        
    def _delete_all(self):
        for flow_id in self._store.copy().keys():
            self._delete(flow_id=flow_id)
        

flow_store = InMemoryFlowStore()
