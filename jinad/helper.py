import os
import argparse
from typing import Dict, List, Union

from jina import __default_host__
from jina.helper import get_random_identity
from fastapi import UploadFile

from jinad.models import PeaModel, SinglePodModel, ParallelPodModel


def get_enum_defaults(parser: argparse.ArgumentParser):
    """ Helper function to get all args that have Enum default values """
    from enum import Enum
    all_args = parser.parse_args([])
    enum_args = {}
    for key in vars(all_args):
        if isinstance(parser.get_default(key), Enum):
            enum_args[key] = parser.get_default(key)
    return enum_args


def handle_enums(args: Dict, parser: argparse.ArgumentParser) -> Dict:
    """ Since REST relies on json, reverse conversion of integers to enums is needed """
    default_enums = get_enum_defaults(parser=parser)
    _args = args.copy()
    if 'log_config' in _args:
        _args['log_config'] = parser.get_default('--log-config')

    for key, value in args.items():
        if key in default_enums:
            _enum_type = type(default_enums[key])
            if isinstance(value, int):
                _args[key] = _enum_type(value)
            elif isinstance(value, str):
                _args[key] = _enum_type.from_string(value)
    return _args


def handle_log_id(args: Dict):
    args['log_id'] = args['identity'] if 'identity' in args else get_random_identity()


def handle_remote_host(args: Dict):
    if 'host' in args:
        args['host'] = __default_host__


def pod_to_namespace(args: Union[SinglePodModel, ParallelPodModel]):
    from jina.parsers import set_pod_parser
    parser = set_pod_parser()

    if isinstance(args, ParallelPodModel):
        pod_args = {}
        args = args.dict()
        for pea_type, pea_args in args.items():
            # this is for pea_type: head & tail when None (pod with parallel = 1)
            if pea_args is None:
                pod_args[pea_type] = None

            # this is for pea_type: head & tail when not None (pod with parallel > 1)
            if isinstance(pea_args, Dict):
                pea_args = handle_enums(args=pea_args,
                                        parser=parser)
                handle_log_id(args=pea_args)
                handle_remote_host(args=pea_args)
                pod_args[pea_type] = argparse.Namespace(**pea_args)

            # this is for pea_type: peas (multiple entries)
            if isinstance(pea_args, List):
                pod_args[pea_type] = []
                for current_pea_arg in pea_args:
                    current_pea_arg = handle_enums(args=current_pea_arg,
                                                   parser=parser)
                    handle_log_id(args=current_pea_arg)
                    handle_remote_host(args=current_pea_arg)
                    pod_args[pea_type].append(argparse.Namespace(**current_pea_arg))

        return pod_args

    if isinstance(args, SinglePodModel):
        args = args.dict()
        pod_args = handle_enums(args=args, parser=parser)
        handle_log_id(args=pod_args)
        handle_remote_host(args=pod_args)
        return argparse.Namespace(**pod_args)


def pea_to_namespace(args: Union[PeaModel, Dict]):
    from jina.parsers import set_pea_parser
    parser = set_pea_parser()

    if isinstance(args, PeaModel):
        args = args.dict()

    if isinstance(args, Dict):
        pea_args = handle_enums(args=args, parser=parser)
        handle_log_id(args=pea_args)
        return argparse.Namespace(**pea_args)


def create_meta_files_from_upload(current_file: UploadFile):
    with open(current_file.filename, 'wb') as f:
        f.write(current_file.file.read())


def delete_meta_files_from_upload(current_file: UploadFile):
    if os.path.isfile(current_file.filename):
        os.remove(current_file.filename)
