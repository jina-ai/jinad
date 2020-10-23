import uuid
from typing import List, Dict, Union
from ruamel.yaml import YAML
from contextlib import contextmanager
from jina.peapods.pod import MutablePod

from helper import Flow
from jina.logging import JinaLogger
from models.pod import PodModel
from excepts import FlowYamlParseException, FlowCreationFailed


class InMemoryStore:
    
    _store = {}
    # TODO: Implement fastapi based oauth/bearer security here
    credentials = 'foo:bar'
    _session_token = None
    logger = JinaLogger(context='🏪 STORE')
    
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
        
    def _create(self):
        raise NotImplementedError
    
    def _start(self, context):
        return context.start()
    
    def _close(self, context):
        context.close()
    
    def _delete(self):
        raise NotImplementedError
        
    def _delete_all(self):
        for _id in self._store.copy().keys():
            self._delete(_id)
    

class InMemoryFlowStore(InMemoryStore):
    
    def _create(self, config: Union[str, List[PodModel]] = None):
        """ Creates Flow using List[PodModel] or string based yaml """
        flow_id = uuid.uuid4()

        if isinstance(config, str):
            yaml = YAML()
            try:
                yaml.register_class(Flow)
                flow = yaml.load(config)
            except Exception as e:
                self.logger.error(f'Got error while loading from yaml {e}')
                raise FlowYamlParseException

        if isinstance(config, list):
            flow = Flow()
            try:
                flow = self._build_with_pods(flow=flow, 
                                             pod_args=config)
            except Exception as e:
                self.logger.error(f'Got error while creating flows via pods {e}')
                raise FlowCreationFailed

        flow = self._start(context=flow)
        self._store[flow_id] = flow
        self.logger.info(f'Started flow with flow_id {flow_id}')
        return flow_id, flow.host, flow.port_expose
    
    def _build_with_pods(self, 
                         flow: Flow, 
                         pod_args: List[PodModel]):
        """ Since we rely on PodModel, this can accept all params that a Pod can accept """
        for current_pod_args in pod_args:
            _current_pod_args = current_pod_args.dict()
            _current_pod_args.pop('log_config')
            flow = flow.add(**_current_pod_args)
        return flow
    
    def _get(self, flow_id):
        """ Fetches a Flow from the store """
        if flow_id not in self._store:
            raise KeyError(f'{flow_id} not found')
        flow = self._store[flow_id]
        return flow.host, flow.port_expose
        
    def _delete(self, flow_id):
        """ Closes a Flow context & deletes from store """
        if flow_id not in self._store:
            raise KeyError(f'flow_id {flow_id} not found in store. please create one!')
        flow = self._store.pop(flow_id)
        self._close(context=flow)
        self.logger.info(f'Closed flow with flow_id {flow_id}')


class InMemoryPodStore(InMemoryStore):
    
    def _create(self, pod_arguments: Dict):
        """ Creates MutablePod via Flow """
        pod_id = uuid.uuid4()
        pod = MutablePod(args=pod_arguments)
        pod = self._start(context=pod)
        self._store[pod_id] = pod
        self.logger.info(f'Started pod with pod_id {pod_id}')
        return pod_id

    def _delete(self, pod_id):
        """ Closes a Pod context & deletes from store """
        if pod_id not in self._store:
            raise KeyError(f'pod_id {pod_id} not found in store. please create one!')
        pod = self._store.pop(pod_id)
        self._close(context=pod)
        self.logger.info(f'Closed flow with flow_id {pod_id}')


flow_store = InMemoryFlowStore()
pod_store = InMemoryPodStore()
