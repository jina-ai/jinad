from pydantic import BaseSettings, validator


class BaseConfig(BaseSettings):
    class Config:
        env_prefix = 'JINAD_'


class FastAPIConfig(BaseConfig):
    NAME: str = 'Jina Flow Manager'
    DESCRIPTION: str = 'REST API for creating/deleting Jina Flow'
    VERSION: str = '0.1.0'
    PREFIX: str = '/v1'
    

class OpenAPITags(BaseConfig):
    FLOW_API_TAGS: list = [{
        "name": "Flow Manager",
        "description": "API to invoke local/remote Flows",
        "externalDocs": {
            "description": "Jina Flow Context Manager",
            "url": "https://docs.jina.ai/chapters/flow/index.html",
        },
    }]
    POD_API_TAGS: list = [{
        "name": "Remote Pod Manager",
        "description": "API to invoke remote Pods (__should be used by Flow APIs only__)",
        "externalDocs": {
            "description": "Jina 101",
            "url": "https://docs.jina.ai/chapters/101/.sphinx.html",
        },
    }]
    LOG_API_TAGS: list = [{
        "name": "logs",
        "description": "Endpoint to get streaming logs from flows/pods",
    }]


class HypercornConfig(BaseConfig):
    HOST: str = '0.0.0.0'
    PORT: int = 8000


class JinaDConfig(BaseConfig):
    CONTEXT: str = 'flow'

    @validator('CONTEXT')
    def name_must_contain_space(cls, value):
        if value.lower() not in ['flow', 'pod']:
            raise ValueError('CONTEXT must be either flow or pod')
        return value.lower()


jinad_config = JinaDConfig()
fastapi_config = FastAPIConfig()
hypercorn_config = HypercornConfig()
openapitags_config = OpenAPITags()
