import uuid
from tempfile import SpooledTemporaryFile
from typing import List, Dict, Union
from ruamel.yaml import YAML
from contextlib import contextmanager
from jina.helper import yaml, colored
from jina.logging import JinaLogger
from jina.peapods.pod import MutablePod
from fastapi import UploadFile

from helper import Flow, create_meta_files_from_upload, delete_meta_files_from_upload
from models.pod import PodModel
from excepts import FlowYamlParseException, FlowCreationFailed, FlowStartFailed, \
    ExecutorFailToLoad, PeaFailToStart, PodStartFailed


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
    
    def _create(self,
                config: Union[str, SpooledTemporaryFile, List[PodModel]] = None,
                files: List[UploadFile] = None):
        """ Creates Flow using List[PodModel] or yaml spec """
        flow_id = uuid.uuid4()

        # This makes sure `uses` & `py_modules` are created locally in `cwd`
        # TODO: Handle file creation, deletion better
        if files:
            [create_meta_files_from_upload(current_file) for current_file in files]

        # FastAPI treats UploadFile as a tempfile.SpooledTemporaryFile
        if isinstance(config, str) or isinstance(config, SpooledTemporaryFile):
            yamlspec = config.read().decode() if isinstance(config, SpooledTemporaryFile) else config
            try:
                yaml.register_class(Flow)
                flow = yaml.load(yamlspec)
            except Exception as e:
                self.logger.error(f'Got error while loading from yaml {repr(e)}')
                raise FlowYamlParseException

        if isinstance(config, list):
            try:
                flow = Flow()
                flow = self._build_with_pods(flow=flow, 
                                             pod_args=config)
            except Exception as e:
                self.logger.error(f'Got error while creating flows via pods: {repr(e)}')
                raise FlowCreationFailed

        try:
            flow = self._start(context=flow)
        except PeaFailToStart as e:
            self.logger.critical(f'Flow couldn\'t get started - Invalid Pod {repr(e)} ')
            self.logger.critical('Possible causes - invalid/not uploaded pod yamls & pymodules')
            # TODO: Send correct error message
            raise FlowStartFailed(repr(e))
        except Exception as e:
            self.logger.critical(f'Got following error while starting the flow: {repr(e)}')
            raise FlowStartFailed(repr(e))

        self._store[flow_id] = {}
        self._store[flow_id]['flow'] = flow
        self._store[flow_id]['files'] = files
        self.logger.info(f'Started flow with flow_id {colored(flow_id, "cyan")}')
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
    
    def _get(self,
             flow_id: uuid.UUID,
             yaml_only: bool = False):
        """ Fetches a Flow from the store """
        if flow_id not in self._store:
            raise KeyError(f'{flow_id} not found')

        if 'flow' in self._store[flow_id]:
            flow = self._store[flow_id]['flow']

        return flow.host, flow.port_expose, flow.yaml_spec
        
    def _delete(self, flow_id: uuid.UUID):
        """ Closes a Flow context & deletes from store """
        if flow_id not in self._store:
            raise KeyError(f'flow_id {flow_id} not found in store. please create one!')
        flow = self._store.pop(flow_id)

        if 'flow' in flow:
            self._close(context=flow['flow'])

        if 'files' in flow:
            for current_file in flow['files']:
                delete_meta_files_from_upload(current_file=current_file)

        self.logger.info(f'Closed flow with flow_id {colored(flow_id, "cyan")}')


class InMemoryPodStore(InMemoryStore):
    
    def _create(self,
                pod_arguments: Dict,
                files: List[UploadFile] = None):
        """ Creates MutablePod via Flow """
        pod_id = uuid.uuid4()
        self._store[pod_id] = {}

        if files:
            [create_meta_files_from_upload(current_file) for current_file in files]
            self._store[pod_id]['files'] = files

        try:
            pod = MutablePod(args=pod_arguments)
            pod = self._start(context=pod)
        except Exception as e:
            self.logger.critical(f'Got following error while starting the pod: {repr(e)}')
            raise PodStartFailed(repr(e))

        self._store[pod_id]['pod'] = pod
        self.logger.info(f'Started pod with pod_id {colored(pod_id, "cyan")}')
        return pod_id
 
    def _delete(self, pod_id: uuid.UUID):
        """ Closes a Pod context & deletes from store """
        if pod_id not in self._store:
            raise KeyError(f'pod_id {pod_id} not found in store. please create one!')
        pod = self._store.pop(pod_id)

        if 'pod' in pod:
            self._close(context=pod['pod'])

        if 'files' in pod:
            for current_file in pod['files']:
                delete_meta_files_from_upload(current_file=current_file)

        self.logger.info(f'Closed pod with pod_id {colored(pod_id, "cyan")}')


flow_store = InMemoryFlowStore()
pod_store = InMemoryPodStore()
