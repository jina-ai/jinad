import uuid
import time
import random
import asyncio
import pathlib
from concurrent.futures import ThreadPoolExecutor

import pytest

from jinad.excepts import HTTPException
from jinad.config import log_config, fastapi_config

LOG_MESSAGE = 'log message'


def feed_path_logs(filepath, total_lines, sleep):
    # method to write logs to a file in random interval
    # this runs in a separate thread
    pathlib.Path(filepath).parent.absolute().mkdir(parents=True, exist_ok=True)
    with open(filepath, 'a') as fp:
        for _ in range(total_lines):
            fp.writelines(LOG_MESSAGE + '\n')
            fp.flush()
            time.sleep(sleep)


@pytest.mark.asyncio
@pytest.mark.parametrize('total_lines, num_lines_to_fetch, sleep', [
    (10, 5, 0.1), (10, 5, random.random()),
    (20, 20, 0.1), (20, 20, random.random()),
    (100, 150, 0.1), (100, 150, random.random())
])
async def test_logging_endpoint_success(fastapi_client, total_lines, num_lines_to_fetch, sleep):
    _id = uuid.uuid1()
    filepath = log_config.PATH % _id

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor,
                                   feed_path_logs,
                                   filepath, total_lines, sleep, )
    time.sleep(2)

    with fastapi_client.websocket_connect(f'{fastapi_config.PREFIX}/wslog/{_id}') as websocket:
        _from = 0
        empty_response_count = 0
        total_number_of_logs = 0
        while True:
            if empty_response_count > 1:
                # disconnect from websocket if there are more than 2 empty responses consecutively
                assert total_number_of_logs == total_lines
                break
            websocket.send_json({'from': _from, 'to': _from + num_lines_to_fetch})
            data = websocket.receive_json()
            if not data:
                empty_response_count += 1
            else:
                total_number_of_logs += len(data)
                assert len(set(data.values())) == 1
                _from = int(list(data.keys())[-1]) + 1
                empty_response_count = 0
            await asyncio.sleep(0.5)

    pathlib.Path(filepath).unlink()


@pytest.mark.asyncio
async def test_logging_endpoint_invalid_id(fastapi_client):
    _id = uuid.uuid1()
    with pytest.raises(HTTPException) as response:
        with fastapi_client.websocket_connect(f'{fastapi_config.PREFIX}/wslog/{_id}') as websocket:
            pass
    assert response.value.status_code == 404
    assert response.value.detail == 'No logs found'
