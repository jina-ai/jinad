from pydantic import BaseSettings


class FastAPIConfig(BaseSettings):
    NAME: str = 'Jina Flow Manager'
    DESCRIPTION: str = 'REST API for creating/deleting Jina Flow'
    VERSION: str = '0.1.0'
    PREFIX: str = 'v1'


class HypercornConfig(BaseSettings):
    HOST: str = '0.0.0.0'
    PORT: int = 8000


fastapi_config = FastAPIConfig()
hypercorn_config = HypercornConfig()
