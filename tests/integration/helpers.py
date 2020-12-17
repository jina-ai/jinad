import json
import os
from pathlib import Path
import requests


def start_docker_compose(file_path):
    os.system(f"docker-compose -f {file_path} --project-directory . up  --build -d")


def stop_docker_compose(file_path):
    os.system(f"docker-compose -f {file_path} --project-directory . down")


def call_api(method, url, payload=None, headers={"Content-Type": "application/json"}):
    return getattr(requests, method)(
        url, data=json.dumps(payload), headers=headers
    ).json()


def get_results(query, top_k=10):
    return call_api(
        method="post",
        url="http://0.0.0.0:45678/api/search",
        payload={"top_k": top_k, "data": [query]},
    )


def send_flow(flow_yaml, pod_dir):
    uses_files = [
        ("uses_files", open(file_path)) for file_path in Path(pod_dir).glob("*.yml")
    ]
    pymodules_files = [
        ("pymodules_files", open(file_path))
        for file_path in Path(pod_dir).rglob("*.py")
    ]

    files = [
        *uses_files,
        *pymodules_files,
        ("yamlspec", open(flow_yaml)),
    ]
    return requests.put("http://localhost:8000/v1/flow/yaml", files=files).json()
