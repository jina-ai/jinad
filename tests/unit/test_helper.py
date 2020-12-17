import pytest
from jina.enums import BetterEnum
from argparse import ArgumentParser

from jinad.helper import get_enum_defaults, handle_enums, flowpod_to_namespace, basepod_to_namespace, PodModel, \
    basepea_to_namespace, PeaModel


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


def test_flowpod_to_namespace():
    pod_dict = {
        'head': {
            'uses': '_route',
            'parallel': 1
        },
        'tail': {
            'uses': '_reduce',
            'parallel': 1
        },
        'peas': [{
            'uses': 'Encoder',
            'pea_id': 1
        },
            {
                'uses': 'Indexer',
                'pea_id': 2
            },
        ]
    }

    pod_args = flowpod_to_namespace(pod_dict)

    assert len(pod_args) == 3
    head_args = pod_args['head']
    assert 'log_id' in head_args
    assert head_args.parallel == 1
    assert head_args.uses == '_route'

    tail_args = pod_args['tail']
    assert 'log_id' in tail_args
    assert tail_args.parallel == 1
    assert tail_args.uses == '_reduce'

    assert len(pod_args['peas']) == 2
    pea_1 = pod_args['peas'][0]
    assert 'log_id' in pea_1
    assert pea_1.uses == 'Encoder'
    assert pea_1.pea_id == 1

    pea_2 = pod_args['peas'][1]
    assert 'log_id' in pea_2
    assert pea_2.uses == 'Indexer'
    assert pea_2.pea_id == 2


def test_basepod_to_namespace():
    pod_args = basepod_to_namespace(PodModel())
    assert 'identity' in pod_args
    assert 'port_expose' in pod_args
    assert 'uses' in pod_args
    assert 'parallel' in pod_args


def test_basepea_to_namespace():
    pea_args = basepea_to_namespace(PeaModel())
    assert 'identity' in pea_args
    assert 'port_expose' in pea_args
    assert 'uses' in pea_args
    assert 'py_modules' in pea_args
    assert 'parallel' not in pea_args
