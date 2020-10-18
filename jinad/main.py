import uvloop
import asyncio
from typing import Any

from fastapi import FastAPI
from hypercorn.config import Config
from hypercorn.asyncio import serve

from api.endpoints import flow, remotepod
from config import fastapi_config, hypercorn_config


def main(invocation: str = 'flow'):
    """Entrypoint to the api

    Args:
        invocation (str, optional): app to point to flow/pod router. Defaults to 'flow'.
    """
    
    app = FastAPI(
        title=fastapi_config.NAME,
        description=fastapi_config.DESCRIPTION,
        version=fastapi_config.VERSION
    )
    
    if invocation == 'flow':
        app.include_router(router=flow.router)
                        #    prefix=fastapi_config.VERSION)
    elif invocation == 'pod':
        app.include_router(router=remotepod.router)
                        #    prefix=fastapi_config.VERSION)
    
    hc_serve(f_app=app)

    
def hc_serve(f_app: 'FastAPI'):
    """Sets uvloop as current eventloop, triggers `hypercorn.serve` using asyncio

    Args:
        f_app (FastAPI): FastAPI app object to be served using hypercorn
    """
    config = Config()
    config.bind = [f'{hypercorn_config.HOST}:{hypercorn_config.PORT}'] 
    
    asyncio.set_event_loop_policy(
        uvloop.EventLoopPolicy()
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        serve(f_app, config)
    )


if __name__ == "__main__":
    main(invocation='flow')
