import argparse
import os
from typing import Dict

from jina.helper import get_random_identity
from fastapi import UploadFile

from jinad.models.pea import PeaModel
from jinad.models.pod import PodModel


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


def flowpod_to_namespace(args: Dict):
    # TODO: combine all 3 to_namespace methods
    from jina.parser import set_pod_parser
    parser = set_pod_parser()
    pod_args = {}

    for pea_type, pea_args in args.items():
        # this is for pea_type: head & tail when None
        if pea_args is None:
            pod_args[pea_type] = None

        # this is for pea_type: head & tail when not None
        if isinstance(pea_args, dict):
            pea_args = handle_enums(args=pea_args,
                                    parser=parser)
            handle_log_id(args=pea_args)
            pod_args[pea_type] = argparse.Namespace(**pea_args)

        # this is for pea_type: peas (multiple entries)
        if isinstance(pea_args, list):
            pod_args[pea_type] = []
            for pea_arg in pea_args:
                pea_arg = handle_enums(args=pea_arg,
                                       parser=parser)
                handle_log_id(args=pea_arg)
                pod_args[pea_type].append(argparse.Namespace(**pea_arg))

    return pod_args


def basepod_to_namespace(args: PodModel):
    from jina.parser import set_pod_parser
    parser = set_pod_parser()

    if isinstance(args, PodModel):
        pod_args = handle_enums(args=args.dict(),
                                parser=parser)
        handle_log_id(args=pod_args)
        return argparse.Namespace(**pod_args)


def basepea_to_namespace(args: PeaModel):
    from jina.parser import set_pea_parser
    parser = set_pea_parser()

    if isinstance(args, PeaModel):
        pea_args = handle_enums(args=args.dict(),
                                parser=parser)
        handle_log_id(args=pea_args)
        return argparse.Namespace(**pea_args)


def create_meta_files_from_upload(current_file: UploadFile):
    with open(current_file.filename, 'wb') as f:
        f.write(current_file.file.read())


def delete_meta_files_from_upload(current_file: UploadFile):
    if os.path.isfile(current_file.filename):
        os.remove(current_file.filename)
