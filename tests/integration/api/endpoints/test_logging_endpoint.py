import pytest
import os
import asyncio

from httpx import AsyncClient
from jinad.config import log_config

cur_dir = os.path.dirname(os.path.abspath(__file__))
LOG_MESSAGE = 'log message'


async def feed_path_logs(path):
    for i in range(0, 100):
        os.makedirs(path, exist_ok=True)
        file = os.path.join(path, 'log.log')
        with open(file, 'a') as fp:
            fp.write(LOG_MESSAGE)
            fp.flush()
            await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_logging_endpoint(tmpdir, monkeypatch):
    monkeypatch.setattr(log_config, 'LOG_BASE_PATH', tmpdir)
    path = os.path.join(tmpdir, 'log_id')

    from jinad.main import get_app
    app = get_app()
    async with AsyncClient(app=app, base_url='http://test') as ac:
        response = await asyncio.gather(feed_path_logs(path), ac.get('/log/log_id'))
    assert response[-1].status_code == 200
    # assert response[-1].json() == {"message": "Tomato"}
