import os
import argparse
from typing import Dict, Union

from jina.helper import get_random_identity
from fastapi import UploadFile

from jinad.models import PeaModel, PodModel


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


def pod_to_namespace(args: Union[PodModel, Dict]):
    from jina.parsers import set_pod_parser
    parser = set_pod_parser()

    if isinstance(args, PodModel):
        args = args.dict()

    if isinstance(args, Dict):
        pod_args = handle_enums(args=args, parser=parser)
        handle_log_id(args=pod_args)
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
