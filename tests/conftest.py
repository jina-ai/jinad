import os
import sys
import pytest
from fastapi.testclient import TestClient

# adding jinad root to sys path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../jinad')
from jinad.config import fastapi_config
PREFIX = fastapi_config.PREFIX


@pytest.fixture(scope='session')
def fastapi_client():
    from jinad.main import get_app
    app = get_app()
    client = TestClient(app)
    return client


@pytest.fixture(scope='session')
def common_endpoints():
    return [
        ('openapi', '/openapi.json'),
        ('swagger_ui_html', '/docs'),
        ('swagger_ui_redirect', '/docs/oauth2-redirect'),
        ('redoc_html', '/redoc'),
        ('_status', f'{PREFIX}/alive'),
        ('_websocket_logs', f'{PREFIX}/wslog/{{log_id}}')
    ]


@pytest.fixture(scope='session')
def flow_endpoints():
    return [
        ('_create_from_pods', f'{PREFIX}/flow/pods'),
        ('_create_from_yaml', f'{PREFIX}/flow/yaml'),
        ('_fetch', f'{PREFIX}/flow/{{flow_id}}'),
        ('_ping', f'{PREFIX}/ping'),
        ('_delete', f'{PREFIX}/flow'),
    ]


@pytest.fixture(scope='session')
def pod_endpoints():
    return [
        ('_upload', f'{PREFIX}/upload'),
        ('_create_independent', f'{PREFIX}/pod/cli'),
        ('_create_via_flow', f'{PREFIX}/pod/flow'),
        ('_delete', f'{PREFIX}/pod')
    ]


@pytest.fixture(scope='session')
def pea_endpoints():
    return [
        ('_upload', f'{PREFIX}/pea/upload'),
        ('_create', f'{PREFIX}/pea'),
        ('_delete', f'{PREFIX}/pea')
    ]
