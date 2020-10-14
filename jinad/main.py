import uvloop
import asyncio
from typing import Any

from hypercorn.config import Config
from hypercorn.asyncio import serve
from fastapi import FastAPI

from api.api import api_router

app = FastAPI(
    title='Jina Flow Manager',
    description='REST API for creating / deleting Jina Flow',
    version='0.1.0'
)
app.include_router(router=api_router, prefix='/v1')


if __name__ == "__main__":
    config = Config()
    config.bind = ["localhost:8000"] 
    
    asyncio.set_event_loop_policy(
        uvloop.EventLoopPolicy()
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        serve(app, config)
    )
