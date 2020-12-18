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

directory = Path("tests/integration/distributed/test_index_query_with_shards/")
compose_yml = directory / "docker-compose.yml"
flow_yml = directory / "flow.yml"
pod_dir = directory / "pods"


def test_flow():
    if Path.cwd().name != "jinad":
        sys.exit(
            "test_index_query_with_shards.py should only be run from the jinad base directory"
        )

    start_docker_compose(compose_yml)

    time.sleep(10)

    flow_id = send_flow(flow_yml, pod_dir)["flow_id"]

    print(f"Successfully started the flow: {flow_id}. Lets index some data")

    for x in range(100):
        text = "text:hey, dude " + str(x)
        text_indexed = call_api(
            method="post",
            url="http://0.0.0.0:45678/api/index",
            payload={"top_k": 10, "data": [text]},
        )["index"]["docs"][0]["text"]

        assert text_indexed == text

    r = call_api(method="get", url=f"http://localhost:8000/v1/flow/{flow_id}")
    assert r["status_code"] == 200

    r = call_api(
        method="delete", url=f"http://localhost:8000/v1/flow?flow_id={flow_id}"
    )
    assert r["status_code"] == 200

    flow_id = send_flow(flow_yml, pod_dir)["flow_id"]

    print(f"Successfully started the flow: {flow_id}. Lets send some query")

    texts_matched = get_results(query="anything will match the same")

    assert len(texts_matched["search"]["docs"][0]["matches"]) == 10

    r = call_api(method="get", url=f"http://localhost:8000/v1/flow/{flow_id}")
    assert r["status_code"] == 200

    r = call_api(
        method="delete", url=f"http://localhost:8000/v1/flow?flow_id={flow_id}"
    )
    assert r["status_code"] == 200

    stop_docker_compose(compose_yml)
