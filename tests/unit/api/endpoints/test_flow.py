import sys
import uuid
import pytest
from fastapi import UploadFile

from api.endpoints import flow

_temp_id = uuid.uuid1()


def mock_create_success(**kwargs):
    return _temp_id, '0.0.0.0', 12345


def mock_flow_creation_exception(config):
    raise flow.FlowCreationException


def mock_flow_parse_exception(config, files):
    raise flow.FlowYamlParseException


def mock_flow_start_exception(**kwargs):
    raise flow.FlowStartException


def mock_fetch_success(**kwargs):
    return '0.0.0.0', 12345, '!Flow\npods:\n   pod1:\n      uses:_pass'


def mock_fetch_exception(**kwargs):
    raise KeyError


def test_create_from_pods_success(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_create', mock_create_success)
    response = flow._create_from_pods()
    assert response['status_code'] == 200
    assert response['flow_id'] == _temp_id
    assert response['host'] == '0.0.0.0'
    assert response['port'] == 12345
    assert response['status'] == 'started'


def test_create_from_pods_flow_create_exception(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_create', mock_flow_creation_exception)
    with pytest.raises(flow.HTTPException):
        response = flow._create_from_pods()
        assert response['status_code'] == 404
        assert response['detail'] == 'Bad pods args'


def test_create_from_pods_flow_start_exception(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_create', mock_flow_start_exception)
    with pytest.raises(flow.HTTPException):
        response = flow._create_from_pods()
        assert response['status_code'] == 404
        assert response['detail'] == 'Flow couldn\'t get started'


def test_create_from_yaml_success(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_create', mock_create_success)
    response = flow._create_from_yaml(yamlspec=UploadFile(filename='abc.yaml'),
                                      uses_files=[UploadFile(filename='abcd.yaml')],
                                      pymodules_files=[UploadFile(filename='abc.py')])
    assert response['status_code'] == 200
    assert response['flow_id'] == _temp_id
    assert response['host'] == '0.0.0.0'
    assert response['port'] == 12345
    assert response['status'] == 'started'


def test_create_from_yaml_parse_exception(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_create', mock_flow_parse_exception)
    with pytest.raises(flow.HTTPException):
        response = flow._create_from_yaml(yamlspec=UploadFile(filename='abc.yaml'),
                                          uses_files=[UploadFile(filename='abcd.yaml')],
                                          pymodules_files=[UploadFile(filename='abc.py')])
        assert response['status_code'] == 404
        assert response['detail'] == 'Bad pods args'


def test_create_from_yaml_flow_start_exception(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_create', mock_flow_start_exception)
    with pytest.raises(flow.HTTPException):
        response = flow._create_from_yaml(yamlspec=UploadFile(filename='abc.yaml'),
                                          uses_files=[UploadFile(filename='abcd.yaml')],
                                          pymodules_files=[UploadFile(filename='abc.py')])
        assert response['status_code'] == 404
        assert response['detail'] == 'Flow couldn\'t get started'


@pytest.mark.asyncio
async def test_fetch_flow_success(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_get', mock_fetch_success)
    response = await flow._fetch(_temp_id)
    assert response['status_code'] == 200
    assert response['host'] == '0.0.0.0'
    assert response['port'] == 12345
    assert response['yaml'] == '!Flow\npods:\n   pod1:\n      uses:_pass'


@pytest.mark.asyncio
async def test_fetch_flow_success_yaml_only(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_get', mock_fetch_success)
    response = await flow._fetch(_temp_id, yaml_only=True)
    assert response.status_code == 200
    assert response.body == b'!Flow\npods:\n   pod1:\n      uses:_pass'
    assert response.media_type == 'application/yaml'


@pytest.mark.asyncio
async def test_fetch_flow_keyerror(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_get', mock_fetch_exception)
    with pytest.raises(flow.HTTPException):
        response = await flow._fetch(_temp_id)
        assert response['status_code'] == 404
        assert response['detail'] == f'Flow ID {_temp_id} not found! Please create a new Flow'


def mock_ping_exception(**kwargs):
    raise flow.GRPCServerError


def test_ping_success(monkeypatch):
    monkeypatch.setattr(flow, 'py_client', lambda **kwargs: None)
    response = flow._ping(host='0.0.0.0', port=12345)
    assert response['status_code'] == 200
    assert response['detail'] == 'connected'


def test_ping_exception(monkeypatch):
    monkeypatch.setattr(flow, 'py_client', mock_ping_exception)
    with pytest.raises(flow.HTTPException):
        response = flow._ping(host='0.0.0.0', port=12345)
        assert response['status_code'] == 404
        assert response['detail'] == 'Cannot connect to GRPC Server on 0.0.0.0:12345'


def test_delete_flow_success(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_delete', lambda **kwargs: None)
    response = flow._delete(_temp_id)
    assert response['status_code'] == 200


def test_delete_flow_exception(monkeypatch):
    monkeypatch.setattr(flow.flow_store, '_delete', mock_fetch_exception)
    with pytest.raises(flow.HTTPException):
        response = flow._delete(_temp_id)
        assert response['status_code'] == 400
        assert response['detail'] == f'Flow ID {_temp_id} not found! Please create a new Flow'