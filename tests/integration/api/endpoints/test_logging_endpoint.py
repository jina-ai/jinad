import uuid
import time
import random
import pathlib
from multiprocessing import Process
from datetime import datetime, timezone

import pytest
from fastapi import WebSocketDisconnect

from jinad.excepts import HTTPException
from jinad.config import log_config, fastapi_config

LOG_MESSAGE = 'log message'


def feed_path_logs(filepath, total_lines, sleep):
    # method to write logs to a file in random interval
    # this runs in a separate thread
    pathlib.Path(filepath).parent.absolute().mkdir(parents=True, exist_ok=True)
    with open(filepath, 'a', buffering=1) as fp:
        for _ in range(total_lines):
            message = f'{datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")}\t' \
                      f'jina\t' \
                      f'{{"host": "blah", "process": "blah", "message": "{LOG_MESSAGE}" }}'
            fp.writelines(message + '\n')
            time.sleep(sleep)


@pytest.mark.asyncio
@pytest.mark.parametrize('total_lines, sleep, timeout', [
    (5, 1, 2), (10, random.uniform(0.5, 1), 5),
    (20, 1, 2), (20, random.uniform(0.5, 1), 5),
    (100, 1, 2), (100, random.uniform(0.5, 1), 5)
])
async def test_logging_endpoint_success(fastapi_client, total_lines, sleep, timeout):
    log_id = uuid.uuid1()
    filepath = log_config.PATH % log_id

    Process(target=feed_path_logs,
            args=(filepath, total_lines, sleep,),
            daemon=True).start()
    # sleeping for 2 secs to allow the process to write logs
    time.sleep(2)

    with fastapi_client.websocket_connect(f'{fastapi_config.PREFIX}/wslog/{log_id}?timeout={timeout}') as websocket:
        _from = 0
        logs_history = []
        total_number_of_logs = 0
        websocket.send_json({'from': _from})
        while not len(logs_history) == total_lines:
            data = websocket.receive_json()
            assert len(data) == 1
            logs_history.append(data)
            websocket.send_json({})
        # making sure we receive all lines of logs
        assert [int(k) for d in logs_history for k in d] == list(range(1, total_lines + 1))

    pathlib.Path(filepath).unlink()


@pytest.mark.asyncio
@pytest.mark.parametrize('total_lines, sleep, _from', [
    (5, 1, 2), (10, random.random(), 5),
    (20, 0.1, 2), (20, random.random(), 5),
    (100, 0.1, 2), (100, random.random(), 5)
])
async def test_logging_endpoint_from(fastapi_client, total_lines, sleep, _from):
    log_id = uuid.uuid1()
    filepath = log_config.PATH % log_id

    Process(target=feed_path_logs,
            args=(filepath, total_lines, sleep,),
            daemon=True).start()
    # sleeping for 2 secs to allow the thread to write logs
    time.sleep(2)

    with fastapi_client.websocket_connect(f'{fastapi_config.PREFIX}/wslog/{log_id}') as websocket:
        logs_history = []
        total_number_of_logs = 0
        websocket.send_json({'from': _from})
        while not len(logs_history) == total_lines - _from:
            data = websocket.receive_json()
            assert len(data) == 1
            logs_history.append(data)
            websocket.send_json({})

        # making sure we receive all lines of logs
        assert [int(k) for d in logs_history for k in d] == list(range(_from + 1, total_lines + 1))

    pathlib.Path(filepath).unlink()



@pytest.mark.asyncio
@pytest.mark.parametrize('total_lines, sleep, exit_id', [
    (5, 1, 2), (10, random.random(), 5)
])
async def test_logging_endpoint_exit_on_message(fastapi_client, total_lines, sleep, exit_id):
    log_id = uuid.uuid1()
    filepath = log_config.PATH % log_id

    Process(target=feed_path_logs,
            args=(filepath, total_lines, sleep,),
            daemon=True).start()
    # sleeping for 2 secs to allow the thread to write logs
    time.sleep(2)

    with pytest.raises(WebSocketDisconnect) as response:
        with fastapi_client.websocket_connect(f'{fastapi_config.PREFIX}/wslog/{log_id}') as websocket:
            websocket.send_json({})
            c = 0
            message = {}
            while True:
                data = websocket.receive_json()
                assert len(data) == 1
                c += 1
                if c == exit_id:
                    message = {'exit': 1}
                websocket.send_json(message)


@pytest.mark.asyncio
async def test_logging_endpoint_invalid_id(fastapi_client):
    log_id = uuid.uuid1()
    with pytest.raises(HTTPException) as response:
        with fastapi_client.websocket_connect(f'{fastapi_config.PREFIX}/wslog/{log_id}') as websocket:
            pass
    assert response.value.status_code == 404
    assert response.value.detail == 'No logs found'
