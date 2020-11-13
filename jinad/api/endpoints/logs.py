import uuid
import asyncio

from fastapi import APIRouter

from sse_starlette.sse import EventSourceResponse


router = APIRouter()


@router.get(
    path='/log/{id}',
    summary='Stream logs from folder where fluentd stores',
)
async def _log(
        log_id: uuid.UUID
):
    # TODO: How to ever stop this iteration?
    """
    This endpoint is intended to be used from external clients (like dashboard) or from jina Flows or Pods themselves to
    print to log themselves this streamed data.

    :param log_id: The log identifier `flow_id`, `pod_id` or `pea_id` from which to stream logs
    :return:
    """
    file_path = f'/tmp/jina-log/{log_id}/log.log'

    async def _log_stream(file):
        # fluentd creates files under this path with some tag based on day, so as temp solution,
        # just get the first file matching this patter once it appears
        with open(file) as fp:
            fp.seek(0, 2)
            while True:
                readline = fp.readline()
                line = readline.strip()
                if line:
                    yield f'data: {line}\n\n'
                else:
                    await asyncio.sleep(0.1)

    return EventSourceResponse(_log_stream(file_path), media_type='text/event-stream')
