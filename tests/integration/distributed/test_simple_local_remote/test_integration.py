import os
from pathlib import Path
import pytest
import sys
import shutil
import time

from jina import Flow
from tests.helpers import (
    start_docker_compose,
    stop_docker_compose,
    send_flow,
    call_api,
    get_results,
)

directory = Path('tests/integration/distributed/test_simple_local_remote/')
compose_yml = directory / 'docker-compose.yml'
flow_yml = directory / 'flow.yml'
pod_dir = directory / 'pods'

workspace = Path('workspace')
if workspace.exists():
    shutil.rmtree(workspace)

def test_flow():
    if Path.cwd().name != 'jinad':
        sys.exit(
            'test_integration.py should only be run from the jinad base directory'
        )

    os.environ['JINA_ENCODER_HOST'] = 'encoder'
    os.environ['JINA_INDEXER_HOST'] = 'indexer'

    start_docker_compose(compose_yml)

    time.sleep(10)

    with Flow.load_config(str(flow_yml)) as f:
        f.index_lines(['text:cats rulessss'])
    
    f = Flow().load_config(str(flow_yml))
    f.use_rest_gateway()
    with f:
        text_indexed = call_api(
        method='post',
        url='http://0.0.0.0:45678/api/search',
        payload={'top_k': 10, 'data': ['text:cat']},
    )['search']['docs'][0]['text']

    print(text_indexed)


    # flow_id = send_flow(flow_yml, pod_dir)['flow_id']

    # print(f'Successfully started the flow: {flow_id}. Lets index some data')

    # text_indexed = call_api(
    #     method='post',
    #     url='http://0.0.0.0:45678/api/search',
    #     payload={'top_k': 10, 'data': ['text:cats rulessss']},
    # )['search']['docs'][0]['text']

    assert text_indexed == 'text:cats rulessss'

    # r = call_api(method='get', url=f'http://localhost:8000/v1/flow/{flow_id}')
    # assert r['status_code'] == 200

    # r = call_api(
    #     method='delete', url=f'http://localhost:8000/v1/flow?flow_id={flow_id}'
    # )
    # assert r['status_code'] == 200

    # stop_docker_compose(compose_yml)
