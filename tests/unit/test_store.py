from jinad.store import InMemoryPeaStore, InMemoryPodStore
from jina.parser import set_pea_parser, set_pod_parser
from jina.peapods.peas import BasePea
from jina.peapods.pods import BasePod


def test_pea_store():
    args = set_pea_parser().parse_args([])
    store = InMemoryPeaStore()
    with store._session():
        pea_id = store._create(pea_arguments=args)
        assert pea_id in store._store.keys()
        assert isinstance(store._store[pea_id]['pea'], BasePea)
        store._delete(pea_id)
        assert pea_id not in store._store.keys()


def test_pod_store():
    args = set_pod_parser().parse_args([])
    store = InMemoryPodStore()
    with store._session():
        pod_id = store._create(pod_arguments=args)
        assert pod_id in store._store.keys()
        assert isinstance(store._store[pod_id]['pod'], BasePod)
        store._delete(pod_id)
        assert pod_id not in store._store.keys()
