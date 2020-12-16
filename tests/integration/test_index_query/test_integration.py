from pathlib import Path
import pytest
import sys
import time

from ..helpers import start_docker_compose, stop_docker_compose, send_flow, call_api


def test_flow():
    if Path.cwd().name != "jinad":
        sys.exit("test_integration.py should only be run from the jinad base directory")

    start_docker_compose()

    time.sleep(10)

    FLOW_ID = send_flow(flow_yaml="flow.yml", pod_dir="pods")["flow_id"]

    print(f"Successfully started the flow: {FLOW_ID}. Let's index some data")

    TEXT_INDEXED = call_api(
        method="post",
        url="0.0.0.0:45678/api/index",
        payload={"top_k": 10, "data": ["text:hey, dude"]},
    )  # jq -e ".index.docs[] | .text")
    print(f"Indexed document has the text: {TEXT_INDEXED}")

    r = call_api(method="get", url=f"http://localhost:8000/v1/flow/{FLOW_ID}")
    print(r["status_code"])

    r = call_api(
        method="delete", url=f"http://localhost:8000/v1/flow?flow_id={FLOW_ID}"
    )
    print(r["status_code"])

    FLOW_ID = send_flow(flow_yaml="flow.yml", pod_dir="pods")["flow_id"]

    print(f"Successfully started the flow: {FLOW_ID}. Let's send some query")

    TEXT_MATCHED = call_api(
        method="post",
        url="0.0.0.0:45678/api/search",
        payload={"top_k": 10, "data": ["text:anything will match the same"]},
    )  # jq -e ".search.docs[] | .matches[] | .text")

    print(f"document matched has the text: {TEXT_INDEXED}")

    r = call_api(method="get", url=f"http://localhost:8000/v1/flow/{FLOW_ID}")
    print(r["status_code"])

    r = call_api(
        method="delete", url=f"http://localhost:8000/v1/flow?flow_id={FLOW_ID}"
    )
    print(r["status_code"])

    FLOW_ID = send_flow(flow_yaml="flow.yml", pod_dir="pods")["flow_id"]

    r = call_api(method="get", url=f"http://localhost:8000/v1/flow/{FLOW_ID}")
    print(r["status_code"])

    r = call_api(
        method="delete", url=f"http://localhost:8000/v1/flow?flow_id={FLOW_ID}"
    )
    print(r["status_code"])

    stop_docker_compose()

    EXPECTED_TEXT = "text:hey, dude"

    if EXPECTED_TEXT == TEXT_MATCHED:
        print("Success")
    else:
        print("Fail")
        sys.exit(1)