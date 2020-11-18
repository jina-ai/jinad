import uuid
import time
import asyncio
from pathlib import Path
from typing import Optional

from jina.logging import JinaLogger
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from config import log_config
from excepts import HTTPException

logger = JinaLogger(context='👻 LOGS')
router = APIRouter()


@router.websocket(
    path='/wslog/{log_id}'
)
async def _websocket_logs(
    websocket: WebSocket,
    log_id: uuid.UUID,
):
    """
    # TODO: Swagger doesn't support websocket based docs
    Websocket endpoint to stream logs from fluentd file

    ```
    `log_id`: uuid of the flow/pod/pea
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
    try:
        while True:
            data = await websocket.receive_json()
            d = {}
            line_num_from = int(data.get('from', 0))
            line_num_to = int(data.get('to', line_num_from + 5))
            with open(file_path) as fp:
                for line_num, line in enumerate(fp):
                    if line_num > line_num_to:
                        break
                    if line_num_from <= line_num <= line_num_to:
                        d[line_num] = line.strip()
            logger.debug(f'Sending json {d}')
            await websocket.send_json(d)
    except WebSocketDisconnect:
        logger.info(f'Client {client_host}:{client_port} got disconnected!')
