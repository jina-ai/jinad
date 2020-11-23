import uvloop
import asyncio
from collections import namedtuple

from fastapi import FastAPI
from hypercorn.config import Config
from hypercorn.asyncio import serve

from api.endpoints import common_router, flow, pod, pea, logs
from config import jinad_config, fastapi_config, hypercorn_config, openapitags_config


def get_app():
    context = namedtuple('context', ['router', 'openapi_tags', 'tags'])
    _all_routers = {
        'flow': context(router=flow.router,
                        openapi_tags=openapitags_config.FLOW_API_TAGS,
                        tags=[openapitags_config.FLOW_API_TAGS[0]['name']]),
        'pod': context(router=pod.router,
                       openapi_tags=openapitags_config.POD_API_TAGS,
                       tags=[openapitags_config.POD_API_TAGS[0]['name']]),
        'pea': context(router=pea.router,
                       openapi_tags=openapitags_config.PEA_API_TAGS,
                       tags=[openapitags_config.PEA_API_TAGS[0]['name']])
    }
    app = FastAPI(
        title=fastapi_config.NAME,
        description=fastapi_config.DESCRIPTION,
        version=fastapi_config.VERSION
    )
    app.include_router(router=common_router,
                       prefix=fastapi_config.PREFIX)
    app.include_router(router=logs.router,
                       prefix=fastapi_config.PREFIX)
    if jinad_config.CONTEXT == 'all':
        for _current_router in _all_routers.values():
            app.include_router(router=_current_router.router,
                               tags=_current_router.tags,
                               prefix=fastapi_config.PREFIX)
    else:
        _current_router = _all_routers[jinad_config.CONTEXT]
        app.openapi_tags = _current_router.openapi_tags
        app.include_router(router=_current_router.router,
                           tags=_current_router.tags,
                           prefix=fastapi_config.PREFIX)
    return app


def hc_serve(app: 'FastAPI'):
    """Sets uvloop as current eventloop, triggers `hypercorn.serve` using asyncio
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
        serve(app, config)
    )


if __name__ == "__main__":
    app = get_app()
    hc_serve(app=app)
