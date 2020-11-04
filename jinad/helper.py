import os
import argparse
import ruamel.yaml
from typing import List, Dict
from jina.peapods.pea import BasePea
from jina.excepts import FlowTopologyError
from fastapi import UploadFile

from models.pea import PeaModel


def get_enum_defaults(parser: argparse.ArgumentParser):
    """ Helper function to get all args that have Enum default values """
    from enum import Enum
    all_args = parser.parse_args()
    enum_args = {}
    for key in vars(all_args):
        if isinstance(parser.get_default(key), Enum):
            enum_args[key] = parser.get_default(key)
    return enum_args


def handle_enums(args: Dict, parser: argparse.ArgumentParser):
    """ Since REST relies on json, reverse conversion of integers to enums is needed """
    default_enums = get_enum_defaults(parser=parser)
    _args = args.copy()

    if 'log_config' in _args:
        _args.pop('log_config')

    for key, value in args.items():
        if key in default_enums:
            _enum_type = type(default_enums[key])
            if isinstance(value, int):
                _args[key] = _enum_type(value)
            elif isinstance(value, str):
                _args[key] = _enum_type.from_string(value)
    return _args


def pod_dict_to_namespace(args: Dict):
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
            pod_args[pea_type] = argparse.Namespace(**pea_args)

        # this is for pea_type: peas (multiple entries)
        if isinstance(pea_args, list):
            pod_args[pea_type] = []
            for pea_arg in pea_args:
                pea_arg = handle_enums(args=pea_arg,
                                       parser=parser)
                pod_args[pea_type].append(argparse.Namespace(**pea_arg))

    return pod_args


def pea_dict_to_namespace(args: PeaModel):
    from jina.parser import set_pea_parser
    parser = set_pea_parser()

    if isinstance(args, PeaModel):
        pea_args = handle_enums(args=args.dict(),
                                parser=parser)
        return argparse.Namespace(**pea_args)


def create_meta_files_from_upload(current_file: UploadFile):
    with open(current_file.filename, 'wb') as f:
        f.write(current_file.file.read())


def delete_meta_files_from_upload(current_file: UploadFile):
    if os.path.isfile(current_file.filename):
        os.remove(current_file.filename)
