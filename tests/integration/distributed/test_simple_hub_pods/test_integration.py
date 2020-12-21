from pathlib import Path
import pytest
import sys
import time

from tests.helpers import (
    start_docker_compose,
    stop_docker_compose,
    send_flow,
    call_api,
    get_results,
)


directory = Path('tests/integration/distributed/test_simple_hub_pods/')
compose_yml = directory / 'docker-compose.yml'
flow_yml = directory / 'flow.yml'
expected_text = 'text:hey, dude'


@pytest.mark.skip(reason='not working')
def test_simple_hub_pods():
    if Path.cwd().name != 'jinad':
        sys.exit('test_integration.py should only be run from the jinad base directory')

    start_docker_compose(compose_yml)

    time.sleep(10)

    flow_id = send_flow(flow_yml)['flow_id']

    print(f'Successfully started the flow: {flow_id}')

    response = call_api(
        method='post',
        url='http://0.0.0.0:45678/api/search',
        payload={'top_k': 10, 'data': [expected_text]},
    )

    print(f'Response is: {response}')

    text_matched = get_results(query=expected_text)['search']['docs'][0]['text']

    print(f'Returned document has the text: {text_matched}')

    r = call_api(method='get', url=f'http://0.0.0.0:8000/v1/flow/{flow_id}')
    assert r['status_code'] == 200

    r = call_api(method='delete', url=f'http://0.0.0.0:8000/v1/flow?flow_id={flow_id}')
    assert r['status_code'] == 200

    stop_docker_compose(compose_yml)

    assert expected_text == text_matched