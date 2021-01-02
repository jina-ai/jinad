import pytest
from jina.enums import BetterEnum
from argparse import ArgumentParser

from jinad.helper import get_enum_defaults, handle_enums, pod_to_namespace, pea_to_namespace
from jinad.models import PodModel, PeaModel


class SampleEnum(BetterEnum):
    A = 1
    B = 2


parser = ArgumentParser()
parser.add_argument('--arg1', default=SampleEnum.A)
parser.add_argument('--arg2', default=5)


def test_enum_defaults():
    res = get_enum_defaults(parser=parser)
    assert 'arg1' in res
    assert res['arg1'].name == 'A'
    assert res['arg1'].value == 1
    assert 'arg2' not in res


def test_handle_enums():
    args = {'arg1': 2, 'arg2': 6}
    res = handle_enums(args, parser)
    assert 'arg1' in res
    assert res['arg1'] == SampleEnum.B
    assert res['arg2'] == args['arg2']

    args = {'arg1': 3, 'arg2': 6}
    with pytest.raises(ValueError):
        handle_enums(args, parser)


def test_pod_to_namespace():
    pod_args = pod_to_namespace(PodModel())
    assert 'identity' in pod_args
    assert 'port_expose' in pod_args
    assert 'uses' in pod_args
    assert 'parallel' in pod_args


def test_pea_to_namespace():
    pea_args = pea_to_namespace(PeaModel())
    assert 'identity' in pea_args
    assert 'port_expose' in pea_args
    assert 'uses' in pea_args
    assert 'py_modules' in pea_args
    assert 'parallel' not in pea_args
