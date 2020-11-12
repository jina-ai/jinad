import pytest
from jina.enums import BetterEnum
from argparse import ArgumentParser

from jinad.helper import get_enum_defaults, handle_enums


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
    pass


def test_basepod_to_namespace():
    pass


def test_basepea_to_namespace():
    pass
