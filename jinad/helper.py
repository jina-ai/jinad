import os
import copy
import argparse
import ruamel.yaml
from typing import Union, Tuple, List, Dict
from jina.flow import Flow as _Flow
from jina import __default_host__
from jina.peapods.pod import FlowPod as _FlowPod
from jina.peapods.pea import BasePea
from jina.excepts import FlowTopologyError
from fastapi import UploadFile

from jina.enums import PodRoleType


class Flow(_Flow):
    # TODO: no need to copy the whole add function here,
    # we can separate `FlowPod` invocation to a different function & inherit just that
    def add(self,
            needs: Union[str, Tuple[str], List[str]] = None,
            copy_flow: bool = True,
            pod_role: 'PodRoleType' = PodRoleType.POD,
            **kwargs) -> 'Flow':
        """
        Add a pod to the current flow object and return the new modified flow object.
        The attribute of the pod can be later changed with :py:meth:`set` or deleted with :py:meth:`remove`

        Note there are shortcut versions of this method.
        Recommend to use :py:meth:`add_encoder`, :py:meth:`add_preprocessor`,
        :py:meth:`add_router`, :py:meth:`add_indexer` whenever possible.

        :param needs: the name of the pod(s) that this pod receives data from.
                           One can also use 'pod.Gateway' to indicate the connection with the gateway.
        :param pod_role: the role of the Pod, used for visualization and route planning
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the pod CLI supports
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        pod_name = kwargs.get('name', None)

        if pod_name in op_flow._pod_nodes:
            new_name = f'{pod_name}{len(op_flow._pod_nodes)}'
            self.logger.debug(f'"{pod_name}" is used in this Flow already! renamed it to "{new_name}"')
            pod_name = new_name

        if not pod_name:
            pod_name = f'pod{len(op_flow._pod_nodes)}'

        if not pod_name.isidentifier():
            # hyphen - can not be used in the name
            raise ValueError(f'name: {pod_name} is invalid, please follow the python variable name conventions')

        needs = op_flow._parse_endpoints(op_flow, pod_name, needs, connect_to_last_pod=True)

        kwargs.update(op_flow._common_kwargs)
        kwargs['name'] = pod_name

        op_flow._pod_nodes[pod_name] = FlowPod(kwargs=kwargs, needs=needs, pod_role=pod_role)
        op_flow.last_pod = pod_name

        return op_flow


class FlowPod(_FlowPod):
    
    def start(self) -> 'FlowPod':
        if self._args.host == __default_host__:
            return super().start()
        else:
            from remote import RemoteMutablePod
            _remote_pod = RemoteMutablePod(self.peas_args)
            self.enter_context(_remote_pod)
            self.start_sentinels()
            return self


def get_enum_defaults():
    """ Helper function to get all args that have Enum default values """
    from jina.parser import set_pod_parser
    from enum import Enum
    parser = set_pod_parser()
    all_args = parser.parse_args()
    enum_args = {}
    for key in vars(all_args):
        if isinstance(parser.get_default(key), Enum):
            enum_args[key] = parser.get_default(key)
    return enum_args


def handle_enums(args):
    """ Since REST relies on json, reverse conversion of integers to enums is needed """
    default_enums = get_enum_defaults()
    _args = args.copy()

    if 'log_config' in _args:
        _args.pop('log_config')

    for key, value in args.items():
        if key in default_enums:
            _enum_type = type(default_enums[key])
            _args[key] = _enum_type(value)
    return _args


def dict_to_namespace(args: Dict):
    import argparse
    pod_args = {}
    
    for pea_type, pea_args in args.items():
        # this is for pea_type: head & tail when None
        if pea_args is None:
            pod_args[pea_type] = None

        # this is for pea_type: head & tail when not None
        if isinstance(pea_args, dict):
            pea_args = handle_enums(args=pea_args)
            pod_args[pea_type] = argparse.Namespace(**pea_args)

        # this is for pea_type: peas (multiple entries)
        if isinstance(pea_args, list):
            pod_args[pea_type] = []
            for pea_arg in pea_args:
                pea_arg = handle_enums(args=pea_arg)
                pod_args[pea_type].append(argparse.Namespace(**pea_arg))

    return pod_args


def namespace_to_dict(args):
    pea_args = {}
    for k, v in args.items():
        if v is None:
            pea_args[k] = None
        if isinstance(v, argparse.Namespace):
            pea_args[k] = vars(v)
        if isinstance(v, list):
            pea_args[k] = []
            pea_args[k].extend([vars(_) for _ in v]) 
    return pea_args


def create_meta_files_from_upload(current_file: UploadFile):
    with open(current_file.filename, 'wb') as f:
        f.write(current_file.file.read())


def delete_meta_files_from_upload(current_file: UploadFile):
    if os.path.isfile(current_file.filename):
        os.remove(current_file.filename)


def fetch_files_from_yaml(pea_args: Dict):
    if 'peas' in pea_args:
        uses_files = set()
        pymodules_files = set()

        for current_pea in pea_args['peas']:
            if current_pea['uses'] and current_pea['uses'].endswith(('yml', 'yaml')):
                uses_files.add(current_pea['uses'])

            if current_pea['uses_before'] and current_pea['uses_before'].endswith(('yml', 'yaml')):
                uses_files.add(current_pea['uses_before'])

            if current_pea['uses_after'] and current_pea['uses_after'].endswith(('yml', 'yaml')):
                uses_files.add(current_pea['uses_after'])

            if current_pea['py_modules']:
                uses_files.add(current_pea['py_modules'])

        if uses_files:
            for current_file in uses_files:
                if current_file.endswith(('yml', 'yaml')):
                    with open(current_file) as f:
                        result = ruamel.yaml.round_trip_load(f)

                    if 'metas' in result and 'py_modules' in result['metas']:
                        pymodules_files.add(result['metas']['py_modules'])

        return uses_files, pymodules_files
