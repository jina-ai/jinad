import os

import pytest

from ..helpers import (
    send_flow,
    call_api,
    get_results,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_flow(docker_compose):
    flow_id = send_flow(flow_yml, pod_dir)['flow_id']

    for x in range(100):
        text = 'text:hey, dude ' + str(x)
        text_indexed = call_api(
            method='post',
            url='http://0.0.0.0:45678/api/index',
            payload={'top_k': 10, 'data': [text]},
        )['index']['docs'][0]['text']

        assert text_indexed == text

    r = call_api(method='get', url=f'http://localhost:8000/v1/flow/{flow_id}')
    assert r['status_code'] == 200

    r = call_api(
        method='delete', url=f'http://localhost:8000/v1/flow?flow_id={flow_id}'
    )
    assert r['status_code'] == 200

    flow_id = send_flow(flow_yml, pod_dir)['flow_id']

    texts_matched = get_results(query='anything will match the same')

    assert len(texts_matched['search']['docs'][0]['matches']) == 10

    r = call_api(method='get', url=f'http://localhost:8000/v1/flow/{flow_id}')
    assert r['status_code'] == 200

    r = call_api(
        method='delete', url=f'http://localhost:8000/v1/flow?flow_id={flow_id}'
    )
    assert r['status_code'] == 200
