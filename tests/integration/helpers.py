import json
import os
from pathlib import Path
import requests


def start_docker_compose(file_path="docker-compose.yml"):
    file_path = Path(file_path).absolute()
    os.system("docker-compose -f {file_path} --project-directory . up  --build -d")


def stop_docker_compose(file_path="docker-compose.yml"):
    file_path = Path(file_path).absolute()
    os.system("docker-compose -f {file_path} --project-directory . down")


def call_api(method, url, payload=None, headers={"Content-Type": "application/json"}):
    return getattr(requests, method)(
        url, data=json.dumps(payload), headers=headers
    ).json()


def get_results(query, top_k):
    return call_api(
        "http://0.0.0.0:45678/api/search",
        payload={"top_k": top_k, "mode": "search", "data": [f"text:{query}"]},
    )


def send_flow(flow_yaml, pod_dir):
    headers = {"Content-Type": "multipart/form-data", "accept": "application/json"}
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
    return requests.put(
        "http://localhost:8000/v1/flow/yaml", files=files, headers=headers
    ).json()
