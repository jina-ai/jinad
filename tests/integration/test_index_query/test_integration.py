from pathlib import Path
import pytest
import sys
import time

from ..helpers import (
    start_docker_compose,
    stop_docker_compose,
    send_flow,
    call_api,
    get_results,
)


DIRECTORY = Path("tests/integration/test_index_query/")
COMPOSE_YAML = DIRECTORY / "docker-compose.yml"
FLOW_YAML = DIRECTORY / "flow.yml"
POD_DIR = DIRECTORY / "pods"


def test_flow():
    if Path.cwd().name != "jinad":
        sys.exit("test_integration.py should only be run from the jinad base directory")

    start_docker_compose(COMPOSE_YAML)

    time.sleep(10)

    FLOW_ID = send_flow(FLOW_YAML, POD_DIR)["flow_id"]

    print(f"Successfully started the flow: {FLOW_ID}. Let's index some data")

    TEXT_INDEXED = call_api(
        method="post",
        url="http://0.0.0.0:45678/api/index",
        payload={"top_k": 10, "data": ["text:hey, dude"]},
    )["index"]["docs"][0]["text"]

    print(f"Indexed document has the text: {TEXT_INDEXED}")

    r = call_api(method="get", url=f"http://localhost:8000/v1/flow/{FLOW_ID}")
    print(r["status_code"])

    r = call_api(
        method="delete", url=f"http://localhost:8000/v1/flow?flow_id={FLOW_ID}"
    )
    print(r["status_code"])

    FLOW_ID = send_flow(FLOW_YAML, POD_DIR)["flow_id"]

    print(f"Successfully started the flow: {FLOW_ID}. Let's send some query")

    TEXT_MATCHED = get_results(query="text:anything will match the same")["search"][
        "docs"
    ][0]["matches"][0]["text"]

    print(f"document matched has the text: {TEXT_INDEXED}")

    r = call_api(method="get", url=f"http://localhost:8000/v1/flow/{FLOW_ID}")
    print(r["status_code"])

    r = call_api(
        method="delete", url=f"http://localhost:8000/v1/flow?flow_id={FLOW_ID}"
    )
    print(r["status_code"])

    stop_docker_compose(COMPOSE_YAML)

    EXPECTED_TEXT = "text:hey, dude"

    assert EXPECTED_TEXT == TEXT_MATCHED