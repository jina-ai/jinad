import os
import sys
import pytest
from fastapi.testclient import TestClient

# adding jinad root to sys path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../jinad')


@pytest.fixture()
def client():
    from jinad.main import get_app
    app = get_app()
    client = TestClient(app)


@pytest.fixture(scope='session')
def common_endpoints():
    return [
        ('openapi', '/openapi.json'),
        ('swagger_ui_html', '/docs'),
        ('swagger_ui_redirect', '/docs/oauth2-redirect'),
        ('redoc_html', '/redoc'),
        ('_status', '/v1/alive')
    ]


@pytest.fixture(scope='session')
def flow_endpoints():
    return [
        ('_create_from_pods', '/v1/flow/pods'),
        ('_create_from_yaml', '/v1/flow/yaml'),
        ('_fetch', '/v1/flow/{flow_id}'),
        ('_ping', '/v1/ping'),
        ('_delete', '/v1/flow'),
        ('_websocket_logs', '/v1/wslogs')
    ]


@pytest.fixture(scope='session')
def pod_endpoints():
    return [
        ('_upload', '/v1/upload'),
        ('_create_independent', '/v1/pod/cli'),
        ('_create_via_flow', '/v1/pod/flow'),
        ('_log', '/v1/log'),
        ('_delete', '/v1/pod')
    ]


@pytest.fixture(scope='session')
def pea_endpoints():
    return [
        ('_upload', '/v1/pea/upload'),
        ('_create', '/v1/pea'),
        ('_log', '/v1/log'),
        ('_delete', '/v1/pea')
    ]
