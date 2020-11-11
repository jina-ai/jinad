import uuid
import pytest
from fastapi import UploadFile

from api.endpoints import pod

_temp_id = uuid.uuid1()


def mock_pod_start_exception(**kwargs):
    raise pod.PodStartException


def mock_key_error(**kwargs):
    raise KeyError


@pytest.mark.asyncio
async def test_create_independent_success(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_create', lambda **args: _temp_id)
    response = await pod._create_independent(pod.PodModel())
    assert response['status_code'] == 200
    assert response['pod_id'] == _temp_id
    assert response['status'] == 'started'


@pytest.mark.asyncio
async def test_create_independent_pod_start_exception(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_create', mock_pod_start_exception)
    with pytest.raises(pod.HTTPException) as response:
        await pod._create_independent(pod.PodModel())
    assert response.value.status_code == 404
    assert 'Pod couldn\'t get started' in response.value.detail


@pytest.mark.asyncio
async def test_create_independent_any_exception(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_create', mock_key_error)
    with pytest.raises(pod.HTTPException) as response:
        await pod._create_independent(pod.PodModel())
    assert response.value.status_code == 404
    assert response.value.detail == 'Something went wrong'


@pytest.mark.asyncio
async def test_create_via_flow_success(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_create', lambda **args: _temp_id)
    monkeypatch.setattr(pod, 'flowpod_to_namespace', lambda **args: {})
    response = await pod._create_via_flow({})
    assert response['status_code'] == 200
    assert response['pod_id'] == _temp_id
    assert response['status'] == 'started'


@pytest.mark.asyncio
async def test_create_via_flow_pod_start_exception(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_create', mock_pod_start_exception)
    monkeypatch.setattr(pod, 'flowpod_to_namespace', lambda **args: {})
    with pytest.raises(pod.HTTPException) as response:
        await pod._create_via_flow({})
    assert response.value.status_code == 404
    assert 'Pod couldn\'t get started' in response.value.detail


@pytest.mark.asyncio
async def test_create_via_flow_any_exception(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_create', mock_key_error)
    monkeypatch.setattr(pod, 'flowpod_to_namespace', lambda **args: {})
    with pytest.raises(pod.HTTPException) as response:
        await pod._create_via_flow({})
    assert response.value.status_code == 404
    assert response.value.detail == 'Something went wrong'


@pytest.mark.asyncio
async def test_delete_success(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_delete', lambda **kwargs: None)
    response = await pod._delete(_temp_id)
    assert response['status_code'] == 200


@pytest.mark.asyncio
async def test_delete_exception(monkeypatch):
    monkeypatch.setattr(pod.pod_store, '_delete', mock_key_error)
    with pytest.raises(pod.HTTPException) as response:
        await pod._delete(_temp_id)
    assert response.value.status_code == 404
    assert response.value.detail == f'Pod ID {_temp_id} not found! Please create a new Pod'
