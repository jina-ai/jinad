import uuid
from contextlib import contextmanager
from tempfile import SpooledTemporaryFile
from typing import List, Dict, Union
from argparse import Namespace

from fastapi import UploadFile
from jina.flow import Flow
from jina.helper import yaml, colored, get_random_identity
from jina.logging import JinaLogger
from jina.peapods import Runtime, Pod

from jinad.models.pod import PodModel
from jinad.helper import create_meta_files_from_upload, delete_meta_files_from_upload
from jinad.excepts import PeaFailToStart, FlowYamlParseException, FlowCreationException, \
    FlowStartException, PodStartException, PeaStartException, FlowBadInputException


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
        self.logger.debug(f'LOGIN: {token}')
        return token

    def _logout(self, token):
        self.logger.debug(f'LOGOUT: {token}')

    def _create(self, **kwargs):
        raise NotImplementedError

    def _start(self, context):
        return context.start()

    def _close(self, context):
        context.close()

    def _delete(self, id: uuid.UUID):
        raise NotImplementedError

    def _delete_all(self):
        for _id in self._store.copy().keys():
            self._delete(_id)


class InMemoryFlowStore(InMemoryStore):

    def _create(self,
                config: Union[str, SpooledTemporaryFile, List[PodModel]] = None,
                files: List[UploadFile] = None):
        """ Creates Flow using List[PodModel] or yaml spec """
        # This makes sure `uses` & `py_modules` are created locally in `cwd`
        # TODO: Handle file creation, deletion better
        if files:
            [create_meta_files_from_upload(current_file) for current_file in files]

        # FastAPI treats UploadFile as a tempfile.SpooledTemporaryFile
        # I think this needs to be handled by some `FlowBuilder` class, transfrom a yaml_load to a config
        if isinstance(config, str) or isinstance(config, SpooledTemporaryFile):
            yamlspec = config.read().decode() if isinstance(config, SpooledTemporaryFile) else config
            try:
                yaml.register_class(Flow)
                flow = yaml.load(yamlspec)
            except Exception as e:
                self.logger.error(f'Got error while loading from yaml {repr(e)}')
                raise FlowYamlParseException
        elif isinstance(config, list):
            try:
                flow = Flow()
                # it is strange to build from a given flow, it seems like a lazy construction pattern could be used?
                flow = self._build_with_pods(flow=flow,
                                             pod_args=config)
            except Exception as e:
                self.logger.error(f'Got error while creating flows via pods: {repr(e)}')
                raise FlowCreationException
        else:
            raise FlowBadInputException(f'Not valid Flow config input {type(config)}')

        try:
            flow.args.log_id = flow.args.identity if 'identity' in flow.args else get_random_identity()
            flow_id = uuid.UUID(flow.args.log_id)
            flow = self._start(context=flow)
        except PeaFailToStart as e:
            self.logger.critical(f'Flow couldn\'t get started - Invalid Pod {repr(e)} ')
            self.logger.critical('Possible causes - invalid/not uploaded pod yamls & pymodules')
            # TODO: Send correct error message
            raise FlowStartException(repr(e))
        except Exception as e:
            self.logger.critical(f'Got following error while starting the flow: {repr(e)}')
            raise FlowStartException(repr(e))

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

        if 'files' in flow and flow['files']:
            for current_file in flow['files']:
                delete_meta_files_from_upload(current_file=current_file)

        self.logger.info(f'Closed flow with flow_id {colored(flow_id, "cyan")}')


class InMemoryPodStore(InMemoryStore):

    def _create(self, pod_arguments: Union[Dict, Namespace]):
        """ Creates a Pod via Flow or via CLI """

        try:
            pod_id = uuid.UUID(pod_arguments.log_id) if isinstance(pod_arguments, Namespace) \
                else uuid.UUID(pod_arguments['peas'][0].log_id)

            pod = Pod(args=pod_arguments, allow_remote=False)
            pod = self._start(context=pod)
        except Exception as e:
            self.logger.critical(f'Got following error while starting the pod: {repr(e)}')
            raise PodStartException(repr(e))

        self._store[pod_id] = {}
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


class InMemoryPeaStore(InMemoryStore):
    """ Creates Pea on remote  """

    # TODO: Merge this with InMemoryPodStore
    def _create(self, pea_arguments: Union[Dict, Namespace]):
        try:
            pea_id = uuid.UUID(pea_arguments.log_id) if isinstance(pea_arguments, Namespace) \
                else uuid.UUID(pea_arguments['log_id'])
            pea = Runtime(args=pea_arguments, allow_remote=False)
            pea = self._start(context=pea)
        except Exception as e:
            self.logger.critical(f'Got following error while starting the pea: {repr(e)}')
            raise PeaStartException(repr(e))

        self._store[pea_id] = {}
        self._store[pea_id]['pea'] = pea
        self.logger.info(f'Started pea with pea_id {colored(pea_id, "cyan")}')
        return pea_id

    def _delete(self, pea_id: uuid.UUID):
        """ Closes a Pea context & deletes from store """
        if pea_id not in self._store:
            raise KeyError(f'pea_id {pea_id} not found in store. please create one!')
        pea = self._store.pop(pea_id)

        if 'pea' in pea:
            self._close(context=pea['pea'])

        if 'files' in pea:
            for current_file in pea['files']:
                delete_meta_files_from_upload(current_file=current_file)

        self.logger.info(f'Closed pea with pea_id {colored(pea_id, "cyan")}')


flow_store = InMemoryFlowStore()
pod_store = InMemoryPodStore()
pea_store = InMemoryPeaStore()
