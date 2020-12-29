from pathlib import Path
from typing import Optional, Dict

from contextlib import ExitStack
import json
import requests


def call_api(method: str, url: str, payload: Optional[Dict] = None,
             headers: Dict = {'Content-Type': 'application/json'}):
    return getattr(requests, method)(
        url, data=json.dumps(payload), headers=headers
    ).json()


def get_results(query: str, url: str = 'http://0.0.0.0:45678/api/search', method: str = 'post', top_k: int = 10):
    return call_api(
        method=method,
        url=url,
        payload={'top_k': top_k, 'data': [query]},
    )


def send_flow(flow_yaml: str, pod_dir: Optional[str] = None, url: str = 'http://localhost:8000/v1/flow/yaml'):
    with ExitStack() as file_stack:
        pymodules_files = []
        uses_files = []
        if pod_dir is not None:
            uses_files = [
                ('uses_files', file_stack.enter_context(open(file_path))) for file_path in Path(pod_dir).glob('*.yml')
            ]
            pymodules_files = [
                ('pymodules_files', file_stack.enter_context(open(file_path)))
                for file_path in Path(pod_dir).rglob('*.py')
            ]

        files = [
            *uses_files,
            *pymodules_files,
            ('yamlspec', file_stack.enter_context(open(flow_yaml))),
        ]
        ret = requests.put(url, files=files).json()

    return ret
