import uvloop
import asyncio
from typing import Any

from fastapi import FastAPI
from hypercorn.config import Config
from hypercorn.asyncio import serve

from api.endpoints import common_router, flow, pod, pea
from config import jinad_config, fastapi_config, \
    hypercorn_config, openapitags_config


def main():
    """Entrypoint to the api
    """

    app = FastAPI(
        title=fastapi_config.NAME,
        description=fastapi_config.DESCRIPTION,
        version=fastapi_config.VERSION
    )

    app.include_router(router=common_router,
                       prefix=fastapi_config.PREFIX)

    if jinad_config.CONTEXT == 'flow':
        app.openapi_tags = openapitags_config.FLOW_API_TAGS
        app.include_router(router=flow.router,
                           prefix=fastapi_config.PREFIX)
    elif jinad_config.CONTEXT == 'pod':
        app.openapi_tags = openapitags_config.POD_API_TAGS
        app.include_router(router=pod.router,
                           prefix=fastapi_config.PREFIX)
    elif jinad_config.CONTEXT == 'pea':
        app.openapi_tags = openapitags_config.PEA_API_TAGS
        app.include_router(router=pea.router,
                           prefix=fastapi_config.PREFIX)

    hc_serve(f_app=app)


def hc_serve(f_app: 'FastAPI'):
    """Sets uvloop as current eventloop, triggers `hypercorn.serve` using asyncio

    Args:
        f_app (FastAPI): FastAPI app object to be served using hypercorn
    """
    config = Config()
    config.bind = [f'{hypercorn_config.HOST}:{hypercorn_config.PORT}']
    config.loglevel = 'ERROR'

    asyncio.set_event_loop_policy(
        uvloop.EventLoopPolicy()
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        serve(f_app, config)
    )


if __name__ == "__main__":
    main()
