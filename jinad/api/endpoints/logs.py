import uuid
import time
import json
import asyncio
from pathlib import Path
from typing import Optional

from jina.logging import JinaLogger
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from jinad.config import log_config
from jinad.excepts import HTTPException, TimeoutException, ClientExit


logger = JinaLogger(context='👻 LOGS')
router = APIRouter()

async def tail(file_handler, line_num_from=0, timeout=5):
    """ asynchronous tail file """
    line_number = 0
    last_log_time = time.time()
    while time.time() - last_log_time < timeout:
        for line in file_handler:
            line_number += 1
            if line_number < line_num_from:
                continue
            yield line_number, line
            last_log_time = time.time()
            await asyncio.sleep(0.01)
    else:
        raise TimeoutException()


@router.websocket(
    path='/wslog/{log_id}'
)
async def _websocket_logs(
    websocket: WebSocket,
    log_id: uuid.UUID,
    timeout: Optional[int] = 5,
    exit_text: Optional[str] = 'exit'
):
    """
    # TODO: Swagger doesn't support websocket based docs
    Websocket endpoint to stream logs from fluentd file

    ```
    `log_id`: uuid of the flow/pod/pea
    `timeout`: max time difference b/w successive log lines (helps in client disconnection)
    `exit_text`: exit the connection if this text is found in the message
    ```
    """
    file_path = log_config.PATH % log_id
    if not Path(file_path).is_file():
        raise HTTPException(status_code=404,
                            detail=f'No logs found')

    await websocket.accept()
    client_host = websocket.client.host
    client_port = websocket.client.port
    logger.info(f'Client {client_host}:{client_port} got connected!')
    data = await websocket.receive_json()
    logger.debug(f'received the first message: {data}')
    line_num_from = int(data.get('from', 0))
    logs_to_be_sent = {}

    try:
        with open(file_path) as fp:
            async for line_number, line in tail(file_handler=fp, timeout=timeout):
                if line_number > line_num_from:
                    logs_to_be_sent[line_number] = line
                    logger.info(f'Sending logs {logs_to_be_sent}')
                    await websocket.send_text(json.dumps(logs_to_be_sent))
                    data = await websocket.receive_json()
                    if exit_text in data:
                        raise ClientExit
                    logs_to_be_sent = {}
    except WebSocketDisconnect:
        logger.info(f'Client {client_host}:{client_port} got disconnected!')
    except TimeoutException:
        await websocket.close()
        logger.info(f'No logs found in last {timeout} secs. Timing out!')
        logger.info(f'Closing client {client_host}:{client_port}!')
    except ClientExit:
        await websocket.close()
        logger.info('Client asked to exit!')
        logger.info(f'Closing client {client_host}:{client_port}!')
