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


DIRECTORY = Path("tests/integration/distributed/test_simple_hub_pods/")
COMPOSE_YAML = DIRECTORY / "docker-compose.yml"
FLOW_YAML = DIRECTORY / "flow.yml"
EXPECTED_TEXT = "text:hey, dude"


@pytest.mark.skip(reason="not working")
def test_simple_hub_pods():
    if Path.cwd().name != "jinad":
        sys.exit("test_integration.py should only be run from the jinad base directory")

    start_docker_compose(COMPOSE_YAML)

    time.sleep(10)

    FLOW_ID = send_flow(FLOW_YAML)["flow_id"]

    print(f"Successfully started the flow: {FLOW_ID}")

    RESPONSE = call_api(
        method="post",
        url="http://0.0.0.0:45678/api/search",
        payload={"top_k": 10, "data": [EXPECTED_TEXT]},
    )

    print(f"Response is: {RESPONSE}")

    TEXT_MATCHED = get_results(query=EXPECTED_TEXT)["search"]["docs"][0]["text"]

    print(f"Returned document has the text: {TEXT_MATCHED}")

    r = call_api(method="get", url=f"http://0.0.0.0:8000/v1/flow/{FLOW_ID}")
    assert r["status_code"] == 200

    r = call_api(method="delete", url=f"http://0.0.0.0:8000/v1/flow?flow_id={FLOW_ID}")
    assert r["status_code"] == 200

    stop_docker_compose(COMPOSE_YAML)

    assert EXPECTED_TEXT == TEXT_MATCHED